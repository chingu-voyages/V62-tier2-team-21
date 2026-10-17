import { NavLink, Link, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import "./Header.css";
import "bootstrap-icons/font/bootstrap-icons.css";
import logoImg from "/ChinguV62Team21LogoImg.png";
import { clearSession, getSession } from "../../util/auth";
import { API_URL } from "../../util/api";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [session, setSession] = useState(() => getSession());
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    setSession(getSession());
  }, [location.pathname]);

  async function handleLogout() {
    if (isLoggingOut) return;

    setIsLoggingOut(true);

    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.session_token}`,
        },
      });
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      clearSession();
      setSession(null);
      setIsMenuOpen(false);
      setIsLoggingOut(false);
      navigate("/", { replace: true });
    }
  }

  function closeMenu() {
    setIsMenuOpen(false);
  }

  return (
    <header className="header">
      <div>
        <Link to="/" onClick={closeMenu}>
          <img src={logoImg} alt="Chingu Team Logo" className="header-logo" />
        </Link>
      </div>

      <button
        type="button"
        className="menu-button"
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        aria-label="Toggle navigation menu"
        aria-expanded={isMenuOpen}
      >
        {isMenuOpen ? (
          <i className="bi bi-x"></i>
        ) : (
          <i className="bi bi-list hamburger-icon"></i>
        )}
      </button>

      <ul
        className={
          isMenuOpen
            ? "header-right-division menu-open"
            : "header-right-division"
        }
      >
        <li className="header-list-item">
          <NavLink
            to="/"
            onClick={closeMenu}
            className={({ isActive }) =>
              isActive ? "nav-link nav-active" : "nav-link"
            }
          >
            Home
          </NavLink>
        </li>

        <li className="header-list-item">Product</li>

        {session ? (
          <>
            <li className="header-list-item">
              <NavLink
                to="/saved-learning-paths"
                onClick={closeMenu}
                className={({ isActive }) =>
                  isActive ? "nav-link nav-active" : "nav-link"
                }
              >
                Saved Paths
              </NavLink>
            </li>

            <li className="header-list-item">
              <button
                type="button"
                className="nav-link header-logout-button"
                onClick={handleLogout}
                disabled={isLoggingOut}
              >
                {isLoggingOut ? "Logging Out..." : "Log Out"}
              </button>
            </li>
          </>
        ) : (
          <li className="header-list-item">
            <NavLink
              to="/login"
              onClick={closeMenu}
              className={({ isActive }) =>
                isActive ? "nav-link nav-active" : "nav-link"
              }
            >
              Sign in
            </NavLink>
          </li>
        )}

        <li className="header-list-item">Help</li>
        <li className="header-list-item">Admin</li>
      </ul>
    </header>
  );
}
