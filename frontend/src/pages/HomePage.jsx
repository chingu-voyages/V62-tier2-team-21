import { useNavigate } from "react-router-dom";
import "./HomePage.css";
import "bootstrap-icons/font/bootstrap-icons.css";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="home-page">
      <div className="hero">
        <h1 className="hero-title">Learning Path to Career</h1>
        <p className="hero-description">
          Welcome! Where do you want your career to go next? <br />
          Start your learning path here.
        </p>
        <button
          className="get-started-button"
          onClick={() => navigate("/login")}
        >
          <i className="bi bi-door-open-fill"></i>
          <p>Get Started</p>
        </button>
      </div>
    </div>
  );
}
