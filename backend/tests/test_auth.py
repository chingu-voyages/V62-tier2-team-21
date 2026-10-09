import hashlib
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import httpx
import psycopg
import pytest
from fastapi.testclient import TestClient

import main

# Captured after `import main` loads backend/.env, so it is the production URL
# (if configured). Tests must never use it.
PRODUCTION_DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATION_PATHS = sorted((Path(__file__).resolve().parent.parent / "migrations").glob("*.sql"))
# Port 1 on localhost refuses connections immediately, so no real database is reached.
UNREACHABLE_DATABASE_URL = "postgresql://invalid:invalid@127.0.0.1:1/none?connect_timeout=2"
SCRYPT_HASH_PATTERN = re.compile(r"^scrypt\$16384\$8\$1\$[0-9a-f]{32}\$[0-9a-f]{128}$")

VALID_USER = {
    "full_name": "Ahmet Sağdaşlı",
    "email": "ahmet@example.com",
    "password": "password123",
}


@pytest.fixture(scope="session")
def test_database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; PostgreSQL tests are skipped.")
    if url == PRODUCTION_DATABASE_URL:
        pytest.fail(
            "TEST_DATABASE_URL must not equal DATABASE_URL: the tests truncate the users table."
        )
    if urlparse(url).hostname not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("TEST_DATABASE_URL must point to a local disposable PostgreSQL instance.")
    with psycopg.connect(url) as connection:
        for migration_path in MIGRATION_PATHS:
            connection.execute(migration_path.read_text(encoding="utf-8"))
    return url


def _truncate_users(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute(
            "TRUNCATE login_rate_limits, user_sessions, saved_learning_path_items, "
            "saved_learning_paths, users RESTART IDENTITY CASCADE"
        )


@pytest.fixture
def database_url(test_database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    _truncate_users(test_database_url)
    yield test_database_url
    _truncate_users(test_database_url)


@pytest.fixture
def api_client(monkeypatch):
    """Client for tests that never reach the database."""
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DATABASE_URL)
    return TestClient(main.app)


@pytest.fixture
def client(database_url):
    return TestClient(main.app)


def _stored_password_hash(url: str) -> str:
    with psycopg.connect(url) as connection:
        return connection.execute("SELECT password_hash FROM users").fetchone()[0]


def _user_count(url: str) -> int:
    with psycopg.connect(url) as connection:
        return connection.execute("SELECT count(*) FROM users").fetchone()[0]


def test_register_creates_user(client):
    response = client.post("/auth/register", json=VALID_USER)

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "full_name": "Ahmet Sağdaşlı",
        "email": "ahmet@example.com",
    }
    assert isinstance(body["id"], int)


def test_register_rejects_duplicate_email(client):
    client.post("/auth/register", json=VALID_USER)

    response = client.post("/auth/register", json=VALID_USER)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email linked to existing account. Please try a different email."
    }


def test_register_rejects_duplicate_email_with_different_case(client, database_url):
    client.post("/auth/register", json=VALID_USER)

    response = client.post(
        "/auth/register",
        json={**VALID_USER, "email": "Ahmet@Example.com"},
    )

    assert response.status_code == 409
    assert _user_count(database_url) == 1


@pytest.mark.parametrize("email", ["not-an-email", "ahmet@", "@example.com", "ahmet example.com"])
def test_register_rejects_invalid_email(api_client, email):
    response = api_client.post("/auth/register", json={**VALID_USER, "email": email})

    assert response.status_code == 422


@pytest.mark.parametrize("field", ["full_name", "email", "password"])
def test_register_requires_all_fields(api_client, field):
    payload = {key: value for key, value in VALID_USER.items() if key != field}

    response = api_client.post("/auth/register", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("password", ["tiny!pw", "x" * 200])
def test_register_validation_error_never_echoes_password(api_client, password):
    response = api_client.post("/auth/register", json={**VALID_USER, "password": password})

    assert response.status_code == 422
    assert password not in response.text
    assert "input" not in response.json()["detail"][0]


def test_register_rejects_blank_full_name(api_client):
    response = api_client.post("/auth/register", json={**VALID_USER, "full_name": "   "})

    assert response.status_code == 422


def test_password_is_not_stored_in_plain_text(client, database_url):
    client.post("/auth/register", json=VALID_USER)

    stored_hash = _stored_password_hash(database_url)

    assert stored_hash != VALID_USER["password"]
    assert VALID_USER["password"] not in stored_hash


def test_password_hash_has_expected_scrypt_format(client, database_url):
    client.post("/auth/register", json=VALID_USER)

    stored_hash = _stored_password_hash(database_url)

    assert SCRYPT_HASH_PATTERN.match(stored_hash)
    _, n, r, p, salt_hex, digest_hex = stored_hash.split("$")
    recomputed = hashlib.scrypt(
        VALID_USER["password"].encode("utf-8"),
        salt=bytes.fromhex(salt_hex),
        n=int(n),
        r=int(r),
        p=int(p),
        dklen=64,
    )
    assert recomputed.hex() == digest_hex


def test_register_response_never_contains_password_or_hash(client):
    response = client.post("/auth/register", json=VALID_USER)

    assert set(response.json()) == {"id", "full_name", "email"}
    assert "password" not in response.text
    assert "scrypt$" not in response.text


def test_database_failure_returns_safe_500(api_client):
    response = api_client.post("/auth/register", json=VALID_USER)

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Could not create the account. Please try again later."
    }
    # Database internals (host, credentials, driver errors) must not reach the client.
    assert "127.0.0.1" not in response.text
    assert "invalid" not in response.text


def test_user_input_validation_is_unchanged(api_client):
    # An invalid body is rejected by request validation before any LLM call is made.
    response = api_client.post("/user-input", json={})

    assert response.status_code == 422
    errors = response.json()["detail"]
    locations = {tuple(error["loc"]) for error in errors}
    assert ("body", "career_goal") in locations
    assert ("body", "current_skill_level") in locations
    assert ("body", "available_time") in locations
    # FastAPI's default format, including "input", must be unchanged for this route.
    assert all("input" in error for error in errors)


def test_health_check_is_unchanged(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "providers": ["openai", "gemini"]}


def test_password_verification_rejects_wrong_or_malformed_hashes():
    password_hash = main.hash_password(VALID_USER["password"])

    assert main.verify_password(VALID_USER["password"], password_hash)
    assert not main.verify_password("wrong-password", password_hash)
    assert not main.verify_password(VALID_USER["password"], "not-a-password-hash")


def test_login_creates_session_and_logout_revokes_it(client):
    client.post("/auth/register", json=VALID_USER)

    login_response = client.post(
        "/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["user"]["email"] == VALID_USER["email"]
    assert len(body["session_token"]) >= 32
    headers = {"Authorization": f"Bearer {body['session_token']}"}
    assert client.get("/auth/me", headers=headers).status_code == 200
    assert client.post("/auth/logout", headers=headers).status_code == 204
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_login_rejects_invalid_credentials_without_leaking_which_field_failed(client):
    client.post("/auth/register", json=VALID_USER)

    for payload in (
        {"email": VALID_USER["email"], "password": "wrong-password"},
        {"email": "missing@example.com", "password": VALID_USER["password"]},
    ):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect Email or Password. Please try again"}


def test_login_locks_account_on_fifth_failed_attempt(client):
    client.post("/auth/register", json=VALID_USER)
    payload = {"email": VALID_USER["email"], "password": "wrong-password"}

    for _ in range(4):
        assert client.post("/auth/login", json=payload).status_code == 401

    fifth_attempt = client.post("/auth/login", json=payload)
    assert fifth_attempt.status_code == 401
    assert fifth_attempt.json() == {"detail": "Incorrect Email or Password. Please try again"}

    blocked_correct_password = client.post(
        "/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert blocked_correct_password.status_code == 401


def test_expired_lock_resets_failed_attempt_counter(client, database_url):
    client.post("/auth/register", json=VALID_USER)
    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            "UPDATE users SET failed_login_attempts = 5, locked_until = now() - interval '1 minute'"
        )

    response = client.post(
        "/auth/login",
        json={"email": VALID_USER["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    with psycopg.connect(database_url) as connection:
        failed_attempts, locked_until = connection.execute(
            "SELECT failed_login_attempts, locked_until FROM users"
        ).fetchone()
    assert failed_attempts == 1
    assert locked_until is None


def _login_attempt(client, ip: str, email: str, password: str = "wrong-password"):
    return client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers={"x-vercel-forwarded-for": ip},
    )


def test_ip_rate_limit_blocks_eleventh_attempt_across_different_accounts(client):
    ip = "203.0.113.5"
    for i in range(main.LOGIN_RATE_LIMIT):
        response = _login_attempt(client, ip, f"nouser{i}@example.com")
        assert response.status_code == 401

    blocked = _login_attempt(client, ip, "nouser-eleventh@example.com")

    assert blocked.status_code == 429


def test_successful_login_does_not_increase_net_ip_attempt_count(client, database_url):
    client.post("/auth/register", json=VALID_USER)
    ip = "198.51.100.7"

    for i in range(3):
        _login_attempt(client, ip, f"nouser{i}@example.com")
    response = _login_attempt(client, ip, VALID_USER["email"], VALID_USER["password"])
    assert response.status_code == 200

    client_hash = hashlib.sha256(f"login:{ip}".encode("utf-8")).hexdigest()
    with psycopg.connect(database_url) as connection:
        attempt_count = connection.execute(
            "SELECT attempt_count FROM login_rate_limits WHERE client_hash = %s", (client_hash,)
        ).fetchone()[0]
    # 3 failed attempts increment by 1 each, the successful one increments then
    # decrements by 1 (net zero), so only the 3 failures should remain counted.
    assert attempt_count == 3


def test_ip_rate_limits_are_tracked_separately_per_ip(client):
    ip_a = "203.0.113.10"
    ip_b = "203.0.113.20"

    for i in range(main.LOGIN_RATE_LIMIT):
        _login_attempt(client, ip_a, f"a{i}@example.com")
    blocked = _login_attempt(client, ip_a, "a-extra@example.com")
    assert blocked.status_code == 429

    still_allowed = _login_attempt(client, ip_b, "b0@example.com")
    assert still_allowed.status_code == 401


def test_ip_rate_limit_resets_after_window_expires(client, database_url):
    ip = "203.0.113.30"
    for i in range(main.LOGIN_RATE_LIMIT):
        _login_attempt(client, ip, f"x{i}@example.com")
    blocked = _login_attempt(client, ip, "blocked@example.com")
    assert blocked.status_code == 429

    with psycopg.connect(database_url, autocommit=True) as connection:
        connection.execute(
            "UPDATE login_rate_limits SET window_started_at = now() - interval '16 minutes'"
        )

    recovered = _login_attempt(client, ip, "after-reset@example.com")
    assert recovered.status_code == 401


def test_rate_limit_block_persists_across_many_subsequent_attempts(client, database_url):
    """Regression guard for the 429-triggers-rollback hypothesis.

    enforce_auth_rate_limit's INSERT/UPDATE runs inside the same `with
    connection:` block as the HTTPException(429) it raises, so psycopg rolls
    that statement back along with everything else. If that rollback ever let
    later requests slip through (instead of just capping the persisted
    counter at the limit), this test would catch it.
    """
    ip = "203.0.113.40"
    for i in range(main.LOGIN_RATE_LIMIT):
        _login_attempt(client, ip, f"y{i}@example.com")

    for i in range(5):
        response = _login_attempt(client, ip, f"still-blocked{i}@example.com")
        assert response.status_code == 429

    client_hash = hashlib.sha256(f"login:{ip}".encode("utf-8")).hexdigest()
    with psycopg.connect(database_url) as connection:
        attempt_count = connection.execute(
            "SELECT attempt_count FROM login_rate_limits WHERE client_hash = %s", (client_hash,)
        ).fetchone()[0]
    # The row-tripping increment is rolled back every time, so the persisted
    # count plateaus at the limit instead of growing with each rejection.
    assert attempt_count == main.LOGIN_RATE_LIMIT


SAMPLE_LEARNING_PATH = [
    {"title": "Step One", "description": "Learn the basics.", "estimated_time": "2 weeks"},
    {"title": "Step Two", "description": "Go deeper.", "estimated_time": "3 weeks"},
]


def _without_ids(items: list[dict]) -> list[dict]:
    return [{k: v for k, v in item.items() if k != "id"} for item in items]


def _auth_headers(client) -> dict:
    client.post("/auth/register", json=VALID_USER)
    login_response = client.post(
        "/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    return {"Authorization": f"Bearer {login_response.json()['session_token']}"}


def test_save_learning_path_requires_authentication(api_client):
    response = api_client.post(
        "/learning-path/save", json={"items": SAMPLE_LEARNING_PATH, "title": "My Path"}
    )

    assert response.status_code == 401


def test_save_learning_path_rejects_empty_selection(client):
    headers = _auth_headers(client)

    response = client.post(
        "/learning-path/save", headers=headers, json={"items": [], "title": "Empty"}
    )

    assert response.status_code == 422


def test_save_learning_path_requires_title(client):
    headers = _auth_headers(client)

    response = client.post(
        "/learning-path/save", headers=headers, json={"items": [SAMPLE_LEARNING_PATH[0]]}
    )

    assert response.status_code == 422


def test_save_learning_path_rejects_blank_title(client):
    headers = _auth_headers(client)

    response = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "   "},
    )

    assert response.status_code == 422


def test_save_learning_path_only_stores_checked_items(client):
    headers = _auth_headers(client)
    checked_items = [SAMPLE_LEARNING_PATH[0]]

    response = client.post(
        "/learning-path/save", headers=headers, json={"items": checked_items, "title": "My Path"}
    )

    assert response.status_code == 201
    body = response.json()
    assert _without_ids(body["items"]) == checked_items
    assert all(isinstance(item["id"], int) for item in body["items"])
    assert isinstance(body["id"], int)


def test_list_saved_learning_paths_returns_most_recent_first(client):
    headers = _auth_headers(client)
    client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "First"},
    )
    client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[1]], "title": "Second"},
    )

    response = client.get("/learning-path/saved", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert _without_ids(body[0]["items"]) == [SAMPLE_LEARNING_PATH[1]]
    assert _without_ids(body[1]["items"]) == [SAMPLE_LEARNING_PATH[0]]


def test_saved_learning_paths_are_isolated_per_user(client, database_url):
    headers = _auth_headers(client)
    client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "My Path"},
    )

    other_user = {**VALID_USER, "email": "other@example.com"}
    client.post("/auth/register", json=other_user)
    other_login = client.post(
        "/auth/login", json={"email": other_user["email"], "password": other_user["password"]}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

    response = client.get("/learning-path/saved", headers=other_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_save_learning_path_strips_title_whitespace(client):
    headers = _auth_headers(client)

    response = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "  My first path  "},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "My first path"


def test_rename_saved_learning_path(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "Original"},
    ).json()

    response = client.patch(
        f"/learning-path/saved/{saved['id']}", headers=headers, json={"title": "Renamed"}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_rename_saved_learning_path_rejects_blank_title(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "Original"},
    ).json()

    response = client.patch(
        f"/learning-path/saved/{saved['id']}", headers=headers, json={"title": "   "}
    )

    assert response.status_code == 422


def test_rename_saved_learning_path_rejects_other_users(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "Original"},
    ).json()

    other_user = {**VALID_USER, "email": "other@example.com"}
    client.post("/auth/register", json=other_user)
    other_login = client.post(
        "/auth/login", json={"email": other_user["email"], "password": other_user["password"]}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

    response = client.patch(
        f"/learning-path/saved/{saved['id']}", headers=other_headers, json={"title": "Hijacked"}
    )

    assert response.status_code == 404


def test_delete_saved_learning_path(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "My Path"},
    ).json()

    response = client.delete(f"/learning-path/saved/{saved['id']}", headers=headers)

    assert response.status_code == 204
    assert client.get("/learning-path/saved", headers=headers).json() == []


def test_delete_saved_learning_path_rejects_other_users(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "My Path"},
    ).json()

    other_user = {**VALID_USER, "email": "other@example.com"}
    client.post("/auth/register", json=other_user)
    other_login = client.post(
        "/auth/login", json={"email": other_user["email"], "password": other_user["password"]}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['session_token']}"}

    response = client.delete(f"/learning-path/saved/{saved['id']}", headers=other_headers)

    assert response.status_code == 404
    assert len(client.get("/learning-path/saved", headers=headers).json()) == 1


def test_delete_saved_learning_path_item_removes_just_that_step(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": SAMPLE_LEARNING_PATH, "title": "My Path"},
    ).json()
    item_id = saved["items"][0]["id"]

    response = client.delete(f"/learning-path/saved/{saved['id']}/items/{item_id}", headers=headers)

    assert response.status_code == 204
    remaining = client.get("/learning-path/saved", headers=headers).json()
    assert len(remaining) == 1
    assert _without_ids(remaining[0]["items"]) == [SAMPLE_LEARNING_PATH[1]]


def test_deleting_the_last_item_deletes_the_saved_path(client):
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "My Path"},
    ).json()
    item_id = saved["items"][0]["id"]

    response = client.delete(f"/learning-path/saved/{saved['id']}/items/{item_id}", headers=headers)

    assert response.status_code == 204
    assert client.get("/learning-path/saved", headers=headers).json() == []


def test_concurrent_deletion_of_last_two_items_still_removes_path(client, database_url):
    """Deleting a path's last two items at the same time must not orphan the path.

    Two requests racing to delete sibling items used to both see the other's
    item as still present and both skip the empty-path cleanup, leaving a
    saved path with zero items.
    """
    headers = _auth_headers(client)
    saved = client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": SAMPLE_LEARNING_PATH, "title": "My Path"},
    ).json()
    item_ids = [item["id"] for item in saved["items"]]

    barrier = threading.Barrier(2)

    def delete_item(item_id: int) -> httpx.Response:
        barrier.wait(timeout=5)
        return TestClient(main.app).delete(
            f"/learning-path/saved/{saved['id']}/items/{item_id}", headers=headers
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(delete_item, item_id) for item_id in item_ids]
        responses = [future.result() for future in futures]

    assert all(response.status_code == 204 for response in responses)
    assert client.get("/learning-path/saved", headers=headers).json() == []
    with psycopg.connect(database_url) as connection:
        assert connection.execute("SELECT count(*) FROM saved_learning_paths").fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM saved_learning_path_items"
        ).fetchone()[0] == 0


def test_delete_account_cascades_sessions_and_saved_paths(client, database_url):
    client.post("/auth/register", json=VALID_USER)
    login = client.post(
        "/auth/login", json={"email": VALID_USER["email"], "password": VALID_USER["password"]}
    )
    headers = {"Authorization": f"Bearer {login.json()['session_token']}"}
    client.post(
        "/learning-path/save",
        headers=headers,
        json={"items": [SAMPLE_LEARNING_PATH[0]], "title": "My Path"},
    )

    response = client.delete("/auth/account", headers=headers)

    assert response.status_code == 204
    assert _user_count(database_url) == 0
    assert client.get("/auth/me", headers=headers).status_code == 401
    with psycopg.connect(database_url) as connection:
        assert connection.execute("SELECT count(*) FROM saved_learning_paths").fetchone()[0] == 0
        assert connection.execute("SELECT count(*) FROM user_sessions").fetchone()[0] == 0
