export default function LoadingContent({ percentage }) {
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

  return (
    <>
      <h2 className="loading-title">Building Your Path</h2>
      <p className="loading-percentage">{displayedPercentage}%</p>
      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${percentage}%` }}></div>
      </div>
      <p className="loading-message">{message}</p>
      <div className="gears">
        <i className="bi bi-gear-fill gear gear-large"></i>
        <i className="bi bi-gear-fill gear gear-small"></i>
      </div>
    </>
  );
}
