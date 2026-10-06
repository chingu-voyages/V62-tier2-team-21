import hashlib
import os
import re
from pathlib import Path

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
    with psycopg.connect(url) as connection:
        for migration_path in MIGRATION_PATHS:
            connection.execute(migration_path.read_text(encoding="utf-8"))
    return url


def _truncate_users(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as connection:
        connection.execute("TRUNCATE users RESTART IDENTITY")


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
    assert fifth_attempt.status_code == 423
    assert fifth_attempt.json() == {"detail": "Account locked temporarily. Please try again later"}

    blocked_correct_password = client.post(
        "/auth/login",
        json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    assert blocked_correct_password.status_code == 423
