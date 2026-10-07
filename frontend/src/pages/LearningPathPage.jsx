import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import "./LearningPathPage.css";
import Footer from "../components/layout/Footer";
import { authHeader, clearSession, getSession } from "../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LearningPathPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const learningPath = location.state?.learningPath;
  const session = getSession();

  const [checkedSteps, setCheckedSteps] = useState(
    () => learningPath?.map(() => false) ?? [],
  );
  const [saveError, setSaveError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [savedCount, setSavedCount] = useState(null);

  if (!learningPath) {
    return <Navigate to="/" replace />;
  }

  function toggleCheck(index) {
    setSavedCount(null);
    setCheckedSteps((prevState) =>
      prevState.map((checked, i) => (i === index ? !checked : checked)),
    );
  }

  async function handleSave() {
    const selectedItems = learningPath.filter((_, index) => checkedSteps[index]);

    if (selectedItems.length === 0) {
      setSaveError("Select at least one step to save.");
      return;
    }

    if (!session) {
      navigate("/login", { state: { from: location } });
      return;
    }

    setSaveError("");
    setIsSaving(true);
    try {
      const response = await fetch(`${API_URL}/learning-path/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ items: selectedItems }),
      });

      if (response.status === 401) {
        clearSession();
        navigate("/login", { state: { from: location } });
        return;
      }
      if (!response.ok) {
        throw new Error("Could not save your learning path. Please try again later.");
      }

      setSavedCount(selectedItems.length);
    } catch (error) {
      setSaveError(error.message);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="learning-path-page">
      <main className="learning-path-container">
        <h2 className="learning-path-title">Your Learning Path</h2>
        <ol className="learning-path-steps">
          {learningPath.map((step, index) => (
            <li className="learning-path-step" key={index}>
              <div className="learning-path-title-container">
                <span className="step-number">{index + 1}.</span>
                <input
                  type="checkbox"
                  checked={checkedSteps[index]}
                  onChange={() => toggleCheck(index)}
                  className="learning-path-check-box"
                  aria-label={`Select ${step.title}`}
                />
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

        {saveError && <p className="learning-path-error">{saveError}</p>}
        {savedCount !== null && (
          <p className="learning-path-success">
            Saved {savedCount} step{savedCount === 1 ? "" : "s"}. View them on your{" "}
            <Link to="/saved-learning-paths">saved learning paths</Link> page.
          </p>
        )}

        <div className="learning-path-actions">
          <button
            type="button"
            className="learning-path-generate-button"
            onClick={() => navigate("/form")}
          >
            ⟳ Generate New Learning Path
          </button>
          <button
            type="button"
            className="learning-path-save-button"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? "Saving…" : "✓ Save"}
          </button>
        </div>
      </main>
      <Footer />
    </div>
  );
}
