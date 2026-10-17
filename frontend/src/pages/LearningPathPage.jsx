import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import "./LearningPathPage.css";
import { authHeader, clearSession, getSession } from "../util/auth";
import { API_URL } from "../util/api";

export default function LearningPathPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const learningPath = location.state?.learningPath;
  const careerGoal = location.state?.careerGoal;

  const [saveError, setSaveError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  if (!Array.isArray(learningPath)) {
    return <Navigate to="/" replace />;
  }

  async function handleSave() {
    if (learningPath.length === 0) {
      setSaveError("There are no steps to save.");
      return;
    }

    if (!getSession()) {
      navigate("/login", {
        state: { from: location },
      });
      return;
    }

    setSaveError("");
    setIsSaving(true);

    try {
      const response = await fetch(`${API_URL}/learning-path/save`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader(),
        },
        body: JSON.stringify({
          title: careerGoal
            ? `My Learning Path - ${careerGoal}`
            : "My Learning Path",
          items: learningPath,
        }),
      });

      if (response.status === 401) {
        clearSession();
        navigate("/login", {
          state: { from: location },
        });
        return;
      }

      if (!response.ok) {
        throw new Error(
          "Could not save your learning path. Please try again later.",
        );
      }

      setIsSaved(true);
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : "An unexpected error occurred.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="learning-path-page">
      <main className="learning-path-container">
        <h2 className="learning-path-title">
          Your Learning Path {careerGoal && ` - ${careerGoal}`}
        </h2>

        <ol className="learning-path-steps">
          {learningPath.map((step, index) => (
            <li className="learning-path-step" key={index}>
              <div className="learning-path-title-container">
                <span className="step-number">{index + 1}.</span>

                <h3 className="learning-path-step-title">{step.title}</h3>
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

        {saveError && (
          <p className="learning-path-error" role="alert">
            {saveError}
          </p>
        )}

        {isSaved && (
          <p className="learning-path-success" role="status">
            Your learning path has been saved successfully. View it on your{" "}
            <Link to="/saved-learning-paths">saved learning paths</Link> page.
          </p>
        )}

        <div className="learning-path-button-container">
          <button
            type="button"
            className="learning-path-button"
            onClick={() => navigate("/form")}
          >
            <i className="bi bi-arrow-repeat"></i>
            Generate New Learning Path
          </button>

          <button
            type="button"
            className="learning-path-button learning-path-save-button"
            onClick={handleSave}
            disabled={isSaving || isSaved}
          >
            {isSaving ? (
              "Saving…"
            ) : isSaved ? (
              <>
                <i className="bi bi-check2"></i>
                Saved
              </>
            ) : (
              <>
                <i className="bi bi-check2"></i>
                Save Learning Path
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
