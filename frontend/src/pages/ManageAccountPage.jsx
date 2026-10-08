import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import "./LearningPathPage.css";
import "./ManageAccountPage.css";
import Footer from "../components/layout/Footer";
import { authHeader, clearSession, getSession } from "../util/auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function ManageAccountPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const session = getSession();

  const [error, setError] = useState("");
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  async function handleDeleteAccount() {
    if (
      !window.confirm(
        "Permanently delete your account and everything you've saved? This cannot be undone.",
      )
    ) {
      return;
    }
    setError("");
    setIsDeletingAccount(true);
    try {
      const response = await fetch(`${API_URL}/auth/account`, {
        method: "DELETE",
        headers: authHeader(),
      });
      if (!response.ok && response.status !== 401) {
        throw new Error(
          "Could not delete your account. Please try again later.",
        );
      }
      clearSession();
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(requestError.message);
      setIsDeletingAccount(false);
    }
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return (
    <div className="learning-path-page">
      <main className="learning-path-container">
        <h2 className="learning-path-title">Manage Account</h2>

        <section className="account-info">
          <div className="account-info-row">
            <span className="account-info-label">Full name</span>
            <span className="account-info-value">{session.user.full_name}</span>
          </div>
          <div className="account-info-row">
            <span className="account-info-label">Email</span>
            <span className="account-info-value">{session.user.email}</span>
          </div>
        </section>

        {error && <p className="learning-path-error">{error}</p>}

        <section className="danger-zone">
          <h3 className="danger-zone-title">Danger Zone</h3>
          <p className="danger-zone-description">
            Permanently delete your account and every learning path you've
            saved. This cannot be undone.
          </p>
          <button
            type="button"
            className="danger-zone-button"
            onClick={handleDeleteAccount}
            disabled={isDeletingAccount}
          >
            {isDeletingAccount ? "Deleting…" : "Delete My Account"}
          </button>
        </section>
      </main>
      <Footer />
    </div>
  );
}
