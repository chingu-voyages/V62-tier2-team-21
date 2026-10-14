import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import "bootstrap-icons/font/bootstrap-icons.css";
import "./SavedLearningPathPage.css";
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
  const [openPathIds, setOpenPathIds] = useState([]);
  const [updatingItemIds, setUpdatingItemIds] = useState([]);
  const [deletingPathIds, setDeletingPathIds] = useState([]);
  const [renamingId, setRenamingId] = useState(null);

  const updatingRef = useRef(new Set());

  function handleUnauthorized() {
    clearSession();
    setSessionExpired(true);
  }

  // Load saved learning paths from the backend
  const loadSavedPaths = useCallback((signal) => {
    fetch(`${API_URL}/learning-path/saved`, {
      headers: authHeader(),
      signal,
    })
      .then(async (response) => {
        if (response.status === 401) {
          clearSession();
          setSessionExpired(true);
          return;
        }

        if (!response.ok) {
          throw new Error("Could not load your saved learning paths.");
        }

        const data = await response.json();
        if (!signal.aborted) {
          setSavedPaths(data);
        }
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") {
          setError(requestError.message);
        }
      });
  }, []);

  useEffect(() => {
    if (!session) return;

    const controller = new AbortController();
    loadSavedPaths(controller.signal);

    return () => controller.abort();
  }, [Boolean(session), loadSavedPaths]);

  // Open or close a saved learning path
  function togglePath(savedPathId) {
    setOpenPathIds((prev) =>
      prev.includes(savedPathId)
        ? prev.filter((id) => id !== savedPathId)
        : [...prev, savedPathId],
    );
  }

  // Start renaming a path
  function startRename(savedPath) {
    setError("");
    setEditingId(savedPath.id);
    setEditingTitle(savedPath.title ?? "");
  }

  // Save the updated path title
  async function handleRenameSubmit(event, savedPathId) {
    event.preventDefault();

    if (renamingId !== null) return;

    setError("");
    setRenamingId(savedPathId);

    try {
      const response = await fetch(
        `${API_URL}/learning-path/saved/${savedPathId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...authHeader(),
          },
          body: JSON.stringify({ title: editingTitle }),
        },
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error("Could not rename the saved learning path.");
      }

      const updated = await response.json();

      setSavedPaths((prev) =>
        prev.map((path) =>
          path.id === savedPathId
            ? { ...path, ...updated, items: path.items }
            : path,
        ),
      );

      setEditingId(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRenamingId(null);
    }
  }

  // Delete an entire learning path
  async function handleDeletePath(savedPathId) {
    if (
      !window.confirm("Delete this saved learning path? This cannot be undone.")
    ) {
      return;
    }

    if (deletingPathIds.includes(savedPathId)) return;

    setError("");
    setDeletingPathIds((prev) => [...prev, savedPathId]);

    try {
      const response = await fetch(
        `${API_URL}/learning-path/saved/${savedPathId}`,
        {
          method: "DELETE",
          headers: authHeader(),
        },
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok && response.status !== 404) {
        throw new Error("Could not delete the saved learning path.");
      }

      setSavedPaths((prev) => prev.filter((path) => path.id !== savedPathId));

      setOpenPathIds((prev) => prev.filter((id) => id !== savedPathId));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setDeletingPathIds((prev) => prev.filter((id) => id !== savedPathId));
    }
  }

  // Update step completion status in the backend
  async function handleToggleCompleted(savedPathId, itemId, completed) {
    const itemKey = `${savedPathId}-${itemId}`;

    if (updatingRef.current.has(itemKey)) return;

    updatingRef.current.add(itemKey);
    setError("");
    setUpdatingItemIds((prev) => [...prev, itemKey]);

    try {
      const response = await fetch(
        `${API_URL}/learning-path/saved/${savedPathId}/items/${itemId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...authHeader(),
          },
          body: JSON.stringify({ completed }),
        },
      );

      if (response.status === 401) {
        handleUnauthorized();
        return;
      }

      if (!response.ok) {
        throw new Error("Could not update step progress.");
      }

      setSavedPaths((prev) =>
        prev.map((path) =>
          path.id === savedPathId
            ? {
                ...path,
                items: path.items.map((item) =>
                  item.id === itemId ? { ...item, completed } : item,
                ),
              }
            : path,
        ),
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      updatingRef.current.delete(itemKey);
      setUpdatingItemIds((prev) => prev.filter((id) => id !== itemKey));
    }
  }

  if (!session || sessionExpired) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return (
    <div className="learning-path-page">
      <main className="learning-path-container">
        <h2 className="learning-path-title">Your Saved Learning Paths</h2>

        {error && (
          <p className="learning-path-error" role="alert">
            {error}
          </p>
        )}

        {savedPaths === null && !error && (
          <p className="learning-path-empty">Loading…</p>
        )}

        {savedPaths?.length === 0 && (
          <p className="learning-path-empty">
            You haven't saved any learning paths yet.
          </p>
        )}

        {savedPaths?.map((savedPath) => {
          const isOpen = openPathIds.includes(savedPath.id);
          const items = savedPath.items ?? [];

          const completedCount = items.filter(
            (item) => item.completed === true,
          ).length;

          return (
            <section className="saved-learning-path-batch" key={savedPath.id}>
              <div className="saved-learning-path-batch-header">
                {editingId === savedPath.id ? (
                  <form
                    className="saved-learning-path-rename-form"
                    onSubmit={(event) =>
                      handleRenameSubmit(event, savedPath.id)
                    }
                  >
                    <input
                      type="text"
                      value={editingTitle}
                      maxLength={200}
                      autoFocus
                      placeholder="Add a title or note"
                      className="saved-learning-path-rename-input"
                      onChange={(event) => setEditingTitle(event.target.value)}
                    />

                    <button
                      type="submit"
                      className="saved-learning-path-icon-button"
                      aria-label="Save title"
                      disabled={renamingId === savedPath.id}
                    >
                      <i className="bi bi-check-lg"></i>
                    </button>

                    <button
                      type="button"
                      className="saved-learning-path-icon-button"
                      aria-label="Cancel"
                      onClick={() => setEditingId(null)}
                      disabled={renamingId === savedPath.id}
                    >
                      <i className="bi bi-x-lg"></i>
                    </button>
                  </form>
                ) : (
                  <>
                    <div className="saved-learning-path-heading">
                      <h3 className="saved-learning-path-batch-title">
                        <button
                          type="button"
                          className="saved-learning-path-toggle"
                          onClick={() => togglePath(savedPath.id)}
                          aria-expanded={isOpen}
                          aria-controls={`saved-path-content-${savedPath.id}`}
                        >
                          <i
                            className="bi bi-chevron-right"
                            aria-hidden="true"
                          ></i>

                          {savedPath.title || "Untitled learning path"}
                        </button>
                      </h3>

                      <p className="saved-learning-path-batch-date">
                        Saved on{" "}
                        {new Date(savedPath.created_at).toLocaleString()}
                      </p>

                      <p className="saved-learning-path-progress">
                        {completedCount} / {items.length} completed
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
                        disabled={deletingPathIds.includes(savedPath.id)}
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  </>
                )}
              </div>

              {/* Accordion content */}
              <div
                id={`saved-path-content-${savedPath.id}`}
                className={`saved-learning-path-content ${
                  isOpen ? "is-open" : ""
                }`}
                inert={!isOpen}
                aria-hidden={!isOpen}
              >
                <div className="saved-learning-path-content-inner">
                  <ol className="learning-path-steps">
                    {items.map((step, index) => {
                      const itemKey = `${savedPath.id}-${step.id}`;
                      const isUpdating = updatingItemIds.includes(itemKey);

                      return (
                        <li className="learning-path-step" key={step.id}>
                          <div className="saved-learning-path-step-header">
                            <span className="step-number">{index + 1}.</span>

                            <input
                              type="checkbox"
                              className="learning-path-check-box"
                              checked={step.completed === true}
                              disabled={isUpdating}
                              onChange={(event) =>
                                handleToggleCompleted(
                                  savedPath.id,
                                  step.id,
                                  event.target.checked,
                                )
                              }
                              aria-label={`Mark ${step.title} as completed`}
                            />

                            <h3 className="learning-path-step-title">
                              {step.title}
                            </h3>

                            {isUpdating && (
                              <span
                                className="saved-learning-path-updating"
                                role="status"
                              >
                                Saving…
                              </span>
                            )}
                          </div>

                          <p className="learning-path-step-description">
                            {step.description}
                          </p>

                          <p className="learning-path-step-time">
                            Estimated time: {step.estimated_time}
                          </p>
                        </li>
                      );
                    })}
                  </ol>
                </div>
              </div>
            </section>
          );
        })}

        <button
          type="button"
          className="learning-path-button"
          onClick={() => navigate("/form")}
        >
          <i className="bi bi-arrow-repeat"></i>
          Generate New Learning Path
        </button>
      </main>
    </div>
  );
}
