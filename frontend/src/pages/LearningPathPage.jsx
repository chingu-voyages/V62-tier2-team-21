import { Navigate, useLocation } from "react-router-dom";
import { useState } from "react";
import "./LearningPathPage.css";

export default function LearningPathPage() {
  const location = useLocation();
  const learningPath = location.state?.learningPath;

  const [completedSteps, setCompletedSteps] = useState(
    () => learningPath?.map(() => false) ?? [],
  );

  if (!learningPath) {
    return <Navigate to="/" replace />;
  }
  function toggleCheck(index) {
    setCompletedSteps((prevState) =>
      prevState.map((step, i) => (i === index ? !step : step)),
    );
  }

  const completedStepsCount = completedSteps.filter((step) => step).length;

  return (
    <div className="learning-path-page">
      <div className="learning-path-container">
        <h2 className="learning-path-title">Your Learning Path</h2>
        <h3 className="learning-path-count">
          {completedStepsCount} / {completedSteps.length} completed
        </h3>
        <ul className="learning-path-steps">
          {learningPath.map((step, index) => (
            <li className="learning-path-step" key={index}>
              <div className="learning-path-title-container">
                <span className="step-number">{index + 1}.</span>
                <input
                  type="checkbox"
                  checked={completedSteps[index]}
                  onChange={() => toggleCheck(index)}
                  className="learning-path-check-box"
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
        </ul>
      </div>
    </div>
  );
}
