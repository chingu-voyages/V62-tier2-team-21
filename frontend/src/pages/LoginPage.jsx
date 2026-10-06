import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Footer from "../components/layout/Footer";
import { saveSession } from "../util/auth";
import "./AuthPage.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15_000);

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        signal: controller.signal,
      });
      const body = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Incorrect Email or Password. Please try again");
        }
        if (response.status === 423) {
          throw new Error("Account locked temporarily. Please try again later");
        }
        throw new Error("Action failed due to network timeout. Please try again");
      }

      saveSession(body);
      navigate("/", { replace: true });
    } catch (requestError) {
      setError(
        requestError.name === "AbortError"
          ? "Action failed due to network timeout. Please try again"
          : requestError.message,
      );
    } finally {
      clearTimeout(timeout);
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <main className="auth-card">
        <Link className="auth-back-link" to="/">
          ← Back to home
        </Link>
        <h1>Sign In</h1>
        <p className="auth-intro">Welcome back. Sign in to access your account.</p>
        <form onSubmit={handleSubmit} noValidate>
          <label htmlFor="login-email">Email address</label>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <label htmlFor="login-password">Password</label>
          <div className="password-input-wrap">
            <input
              id="login-password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button
              className="password-toggle"
              type="button"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
          <Link className="forgot-password-link" to="/forgot-password">
            Forgot password?
          </Link>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in…" : "Login"}
          </button>
        </form>
      </main>
      <Footer />
    </div>
  );
}
