import { NavLink, Link } from "react-router-dom";
import { useState } from "react";
import "./Header.css";
import logoImg from "/ChinguV62Team21LogoImg.png";

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <>
      <header className="header">
        <div>
          <Link to="/">
            <img src={logoImg} alt="Chingu Team Logo" className="header-logo" />
          </Link>
        </div>

        <button
          className="menu-button"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle navigation menu"
          aria-expanded={isMenuOpen}
        >
          {isMenuOpen ? (
            <i class="bi bi-x"></i>
          ) : (
            <i class="bi bi-list hamburger-icon"></i>
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
              className={({ isActive }) =>
                isActive ? "nav-link nav-active" : "nav-link"
              }
            >
              Home
            </NavLink>
          </li>
          <li className="header-list-item">Product</li>
          <li className="header-list-item">Sign in</li>
          <li className="header-list-item">Help</li>
          <li className="header-list-item">Admin</li>
        </ul>
      </header>
    </>
  );
}
