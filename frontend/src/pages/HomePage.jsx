import "./HomePage.css";
import "bootstrap-icons/font/bootstrap-icons.css";

export default function HomePage() {
  return (
    <div className="home-page">
      <main className="hero">
        <h1 className="hero-title">Learning Path to Career</h1>
        <p className="hero-description">
          Welcome! Where do you want your career to go next? <br />
          Start your learning path here.
        </p>
        <button className="get-started-button">
          <i className="bi bi-door-open-fill"></i>
          <p>Get Started</p>
        </button>
      </main>
      <footer className="team-footer">
        <a href="https://github.com/chingu-voyages/V62-tier2-team-21">
          Chingu | V62 | Team 21
        </a>
      </footer>
    </div>
  );
}
