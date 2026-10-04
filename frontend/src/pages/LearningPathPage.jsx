import { Navigate, useLocation } from "react-router-dom";
import "./LearningPathPage.css";

export default function LearningPathPage() {
  const location = useLocation();
  const learningPath = location.state?.learningPath;

  if (!learningPath) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="learning-path-page">
      <div className="learning-path-container">
        <h2 className="learning-path-title">Your Learning Path</h2>
        <ol className="learning-path-steps">
          {learningPath.map((step, index) => (
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
      </div>
    </div>
  );
}
