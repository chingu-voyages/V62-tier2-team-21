import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./Header.css";
import chinguLogo from "../../assets/chingu-logo.png";
import { clearSession, getSession } from "../../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const AUTH_ROUTES = ["/login", "/signup", "/forgot-password"];

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const onAuthRoute = AUTH_ROUTES.includes(location.pathname);

  // Header lives above the router outlet and never remounts between routes,
  // so session is read fresh on every render rather than cached in state.
  // useLocation() already re-renders this on every navigation (e.g. right
  // after AuthPage saves the session and redirects back); logout needs its
  // own nudge since it doesn't navigate anywhere.
  const [, forceRerender] = useState(0);
  const session = getSession();

  async function handleLogout() {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.session_token}` },
      });
    } finally {
      clearSession();
      forceRerender((n) => n + 1);
    }
  }

  return (
    <header className="app-header">
      <Link to="/" className="app-header-logo-link">
        <img className="app-header-logo" src={chinguLogo} alt="Chingu V62 Team 21" />
      </Link>

      {!onAuthRoute && (
        <nav className="app-header-actions">
          {session ? (
            <>
              <span className="app-header-greeting">Hi, {session.user.full_name}</span>
              <button
                className="app-header-button"
                onClick={() => navigate("/saved-learning-paths")}
              >
                Saved Paths
              </button>
              <button className="app-header-button" onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <button className="app-header-button" onClick={() => navigate("/login")}>
                Sign In
              </button>
              <button className="app-header-button" onClick={() => navigate("/signup")}>
                Sign Up
              </button>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
