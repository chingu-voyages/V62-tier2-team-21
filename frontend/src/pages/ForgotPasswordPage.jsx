import { Link } from "react-router-dom";
import Footer from "../components/layout/Footer";
import "./AuthPage.css";

export default function ForgotPasswordPage() {
  return (
    <div className="auth-page">
      <main className="auth-card">
        <Link className="auth-back-link" to="/login">
          ← Back to sign in
        </Link>
        <h1>Forgot Password?</h1>
        <p className="auth-intro">
          Password reset email delivery is being configured. Please check back soon.
        </p>
      </main>
      <Footer />
    </div>
  );
}
