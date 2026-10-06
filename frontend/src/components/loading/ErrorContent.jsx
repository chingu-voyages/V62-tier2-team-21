import "bootstrap-icons/font/bootstrap-icons.css";

export default function ErrorContent({ handleCloseModal, generationError }) {
  const errorContent = {
    timeout: {
      title: "System Maintenance",
      message:
        "We are currently performing scheduled maintenance. Our services will be available again shortly. Please come back later.",
    },
    server: {
      title: "Something Went Wrong",
      message:
        "We couldn't generate your learning path. Please try again later.",
    },
    limit: {
      title: "Daily Limit Reached",
      message:
        "You can generate up to 3 learning paths per day. Please try again tomorrow.",
    },
  };

  const content = errorContent[generationError] ?? errorContent.server;

  return (
    <>
      <i class="bi bi-database-gear error-icon"></i>
      <h2 className="loading-title">{content.title}</h2>
      <p className="loading-message">{content.message}</p>
      <button onClick={handleCloseModal} className="back-to-form-button">
        Back to Form
      </button>
    </>
  );
}
