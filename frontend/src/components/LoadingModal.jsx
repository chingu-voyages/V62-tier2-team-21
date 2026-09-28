import { useState, useEffect } from "react";
import "./LoadingModal.css";

export default function LoadingModal() {
  const [percentage, setPercentage] = useState(0);

  let message = "Building Your Path";
  let displayedPercentage = 0;

  if (percentage >= 100) {
    displayedPercentage = 100;
    message = "Learning Path Ready";
  } else if (percentage >= 70) {
    displayedPercentage = 70;
    message = "Learning Path Ready";
  } else if (percentage >= 30) {
    displayedPercentage = 30;
    message = "Analyzing Skills...";
  }

  useEffect(() => {
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    if (percentage > 100) return;

    const timer = setInterval(() => {
      setPercentage((prev) => (prev < 100 ? prev + 1 : 100));
    }, 100);

    return () => clearInterval(timer);
  }, [percentage]);

  return (
    <div className="back-drop">
      <div className="center-container">
        <h2 className="loading-title">Building Your Path</h2>
        <p className="loading-percentage">{displayedPercentage}%</p>
        <div className="progress-bar-container">
          <div
            className="progress-bar"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <p className="loading-message">{message}</p>
      </div>
    </div>
  );
}
