import { useNavigate } from "react-router-dom";
import "./ErrorPage.css";
import "bootstrap-icons/font/bootstrap-icons.css";

export default function ErrorPage() {
  const navigate = useNavigate();

  return (
    <div className="error-page">
      <div className="error-container">
        <div className="error-icon-wrapper">
          <i className="bi bi-exclamation-circle"></i>
        </div>

        <h1 className="error-title">Something Went Wrong</h1>

        <p className="error-description">
          Oops! Something didn't go as expected.
          <br />
          Please try again or return to the home page.
        </p>

        <button className="error-home-button" onClick={() => navigate("/")}>
          <i className="bi bi-house-door"></i>
          Back to Home
          <i className="bi bi-arrow-right"></i>
        </button>
      </div>
    </div>
  );
}
