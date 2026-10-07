import { useEffect, useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import "./LearningPathPage.css";
import Footer from "../components/layout/Footer";
import { authHeader, clearSession, getSession } from "../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function SavedLearningPathsPage() {
  const location = useLocation();
  const session = getSession();

  const [savedPaths, setSavedPaths] = useState(null);
  const [error, setError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    if (!session) return;

    const controller = new AbortController();

    fetch(`${API_URL}/learning-path/saved`, {
      headers: authHeader(),
      signal: controller.signal,
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
        setSavedPaths(await response.json());
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") {
          setError(requestError.message);
        }
      });

    return () => controller.abort();
  }, [session]);

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
            <h3 className="saved-learning-path-batch-date">
              Saved on {new Date(savedPath.created_at).toLocaleString()}
            </h3>
            <ol className="learning-path-steps">
              {savedPath.items.map((step, index) => (
                <li className="learning-path-step" key={index}>
                  <h3 className="learning-path-step-title">{step.title}</h3>
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
      </main>
      <Footer />
    </div>
  );
}
