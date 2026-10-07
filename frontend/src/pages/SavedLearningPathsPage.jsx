import { useCallback, useEffect, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./LearningPathPage.css";
import Footer from "../components/layout/Footer";
import { authHeader, clearSession, getSession } from "../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function SavedLearningPathsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = getSession();

  const [savedPaths, setSavedPaths] = useState(null);
  const [error, setError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  function handleUnauthorized() {
    clearSession();
    setSessionExpired(true);
  }

  const loadSavedPaths = useCallback(
    (signal) => {
      fetch(`${API_URL}/learning-path/saved`, { headers: authHeader(), signal })
        .then(async (response) => {
          if (response.status === 401) {
            handleUnauthorized();
            return;
          }
          if (!response.ok) {
            throw new Error("Could not load your saved learning paths.");
          }
          setSavedPaths(await response.json());
        })
        .catch((requestError) => {
          if (requestError.name !== "AbortError") {
            setError(requestError.message);
          }
        });
    },
    [],
  );

  useEffect(() => {
    if (!session) return;
    const controller = new AbortController();
    loadSavedPaths(controller.signal);
    return () => controller.abort();
  }, [session, loadSavedPaths]);

  function startRename(savedPath) {
    setError("");
    setEditingId(savedPath.id);
    setEditingTitle(savedPath.title ?? "");
  }

  async function handleRenameSubmit(event, savedPathId) {
    event.preventDefault();
    try {
      const response = await fetch(`${API_URL}/learning-path/saved/${savedPathId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ title: editingTitle }),
      });
      if (response.status === 401) return handleUnauthorized();
      if (!response.ok) throw new Error("Could not rename the saved learning path.");
      const updated = await response.json();
      setSavedPaths((prev) => prev.map((p) => (p.id === savedPathId ? updated : p)));
      setEditingId(null);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleDeletePath(savedPathId) {
    if (!window.confirm("Delete this saved learning path? This cannot be undone.")) return;
    try {
      const response = await fetch(`${API_URL}/learning-path/saved/${savedPathId}`, {
        method: "DELETE",
        headers: authHeader(),
      });
      if (response.status === 401) return handleUnauthorized();
      if (!response.ok && response.status !== 404) {
        throw new Error("Could not delete the saved learning path.");
      }
      setSavedPaths((prev) => prev.filter((p) => p.id !== savedPathId));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleDeleteItem(savedPathId, itemId) {
    try {
      const response = await fetch(
        `${API_URL}/learning-path/saved/${savedPathId}/items/${itemId}`,
        { method: "DELETE", headers: authHeader() },
      );
      if (response.status === 401) return handleUnauthorized();
      if (!response.ok && response.status !== 404) {
        throw new Error("Could not remove that step.");
      }
      setSavedPaths((prev) =>
        prev
          .map((p) =>
            p.id === savedPathId
              ? { ...p, items: p.items.filter((item) => item.id !== itemId) }
              : p,
          )
          .filter((p) => p.id !== savedPathId || p.items.length > 0),
      );
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function handleDeleteAccount() {
    if (
      !window.confirm(
        "Permanently delete your account and everything you've saved? This cannot be undone.",
      )
    ) {
      return;
    }
    setIsDeletingAccount(true);
    try {
      const response = await fetch(`${API_URL}/auth/account`, {
        method: "DELETE",
        headers: authHeader(),
      });
      if (!response.ok && response.status !== 401) {
        throw new Error("Could not delete your account. Please try again later.");
      }
      clearSession();
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      setIsDeletingAccount(false);
    }
  }

  if (!session || sessionExpired) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return (
    <div className="learning-path-page">
      <main className="learning-path-container">
        <h2 className="learning-path-title">Your Saved Learning Paths</h2>

        {error && <p className="learning-path-error">{error}</p>}

        {!error && savedPaths === null && (
          <p className="learning-path-empty">Loading…</p>
        )}

        {savedPaths?.length === 0 && (
          <p className="learning-path-empty">
            You haven't saved any learning path steps yet.
          </p>
        )}

        {savedPaths?.map((savedPath) => (
          <section className="saved-learning-path-batch" key={savedPath.id}>
            <div className="saved-learning-path-batch-header">
              {editingId === savedPath.id ? (
                <form
                  className="saved-learning-path-rename-form"
                  onSubmit={(event) => handleRenameSubmit(event, savedPath.id)}
                >
                  <input
                    type="text"
                    value={editingTitle}
                    maxLength={200}
                    autoFocus
                    placeholder="Add a title or note"
                    onChange={(event) => setEditingTitle(event.target.value)}
                  />
                  <button type="submit" className="saved-learning-path-icon-button" aria-label="Save title">
                    <i className="bi bi-check-lg"></i>
                  </button>
                  <button
                    type="button"
                    className="saved-learning-path-icon-button"
                    aria-label="Cancel"
                    onClick={() => setEditingId(null)}
                  >
                    <i className="bi bi-x-lg"></i>
                  </button>
                </form>
              ) : (
                <>
                  <div>
                    <h3 className="saved-learning-path-batch-title">
                      {savedPath.title || "Untitled learning path"}
                    </h3>
                    <p className="saved-learning-path-batch-date">
                      Saved on {new Date(savedPath.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="saved-learning-path-batch-controls">
                    <button
                      type="button"
                      className="saved-learning-path-icon-button"
                      aria-label="Rename"
                      onClick={() => startRename(savedPath)}
                    >
                      <i className="bi bi-pencil"></i>
                    </button>
                    <button
                      type="button"
                      className="saved-learning-path-icon-button saved-learning-path-icon-button-danger"
                      aria-label="Delete saved learning path"
                      onClick={() => handleDeletePath(savedPath.id)}
                    >
                      <i className="bi bi-trash"></i>
                    </button>
                  </div>
                </>
              )}
            </div>

            <ol className="learning-path-steps">
              {savedPath.items.map((step) => (
                <li className="learning-path-step" key={step.id}>
                  <div className="saved-learning-path-step-header">
                    <h3 className="learning-path-step-title">{step.title}</h3>
                    <button
                      type="button"
                      className="saved-learning-path-icon-button saved-learning-path-icon-button-danger"
                      aria-label={`Remove ${step.title}`}
                      onClick={() => handleDeleteItem(savedPath.id, step.id)}
                    >
                      <i className="bi bi-x-lg"></i>
                    </button>
                  </div>
                  <p className="learning-path-step-description">
                    {step.description}
                  </p>
                  <p className="learning-path-step-time">
                    Estimated time: {step.estimated_time}
                  </p>
                </li>
              ))}
            </ol>
          </section>
        ))}

        <Link className="learning-path-generate-button" to="/form">
          Generate New Learning Path
        </Link>

        <section className="danger-zone">
          <h3 className="danger-zone-title">Danger Zone</h3>
          <p className="danger-zone-description">
            Permanently delete your account and every learning path you've saved.
          </p>
          <button
            type="button"
            className="danger-zone-button"
            onClick={handleDeleteAccount}
            disabled={isDeletingAccount}
          >
            {isDeletingAccount ? "Deleting…" : "Delete My Account"}
          </button>
        </section>
      </main>
      <Footer />
    </div>
  );
}
