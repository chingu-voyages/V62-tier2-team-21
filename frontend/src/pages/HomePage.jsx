import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HomePage.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import Footer from "../components/layout/Footer";
import { clearSession, getSession } from "../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function HomePage() {
  const navigate = useNavigate();
  const [session, setSession] = useState(() => getSession());

  async function handleLogout() {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.session_token}` },
      });
    } finally {
      clearSession();
      setSession(null);
    }
  }

  return (
    <div className="home-page">
      <header className="home-header">
        {session ? (
          <>
            <span>Hi, {session.user.full_name}</span>
            <button className="sign-in-button" onClick={handleLogout}>Log Out</button>
          </>
        ) : (
          <button className="sign-in-button" onClick={() => navigate("/login")}>Sign In</button>
        )}
      </header>
      <main className="hero">
        <h1 className="hero-title">Learning Path to Career</h1>
        <p className="hero-description">
          Welcome! Where do you want your career to go next? <br />
          Start your learning path here.
        </p>
        <button
          className="get-started-button"
          onClick={() => navigate("/form")}
        >
          <i className="bi bi-door-open-fill"></i>
          <p>Get Started</p>
        </button>
      </main>
      <Footer />
    </div>
  );
}
