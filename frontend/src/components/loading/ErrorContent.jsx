import "bootstrap-icons/font/bootstrap-icons.css";

export default function ErrorContent({ handleCloseModal }) {
  return (
    <>
      <i class="bi bi-database-gear error-icon"></i>
      <h2 className="loading-title">System Maintenance</h2>
      <p className="loading-message">
        We are currently performing scheduled maintenance. Our services will be
        available again shortly. Please come back later.
      </p>
      <button onClick={handleCloseModal} className="back-to-form-button">
        Back to Form
      </button>
    </>
  );
}
