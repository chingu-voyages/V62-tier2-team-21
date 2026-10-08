import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "bootstrap-icons/font/bootstrap-icons.css";
import Footer from "../components/layout/Footer";
import { saveSession } from "../util/auth";
import "./AuthPage.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function AuthPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from;
  const mode = location.pathname === "/signup" ? "signup" : "login";

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function switchMode(nextMode) {
    setError("");
    navigate(nextMode === "signup" ? "/signup" : "/login", { state: { from } });
  }

  async function handleLogin(controller) {
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
    return body;
  }

  async function handleSignup(controller) {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: fullName, email, password }),
      signal: controller.signal,
    });
    const body = await response.json();

    if (!response.ok) {
      if (response.status === 409) {
        throw new Error(body.detail);
      }
      if (response.status === 422) {
        const firstError = Array.isArray(body.detail) ? body.detail[0] : null;
        throw new Error(
          firstError?.msg ?? "Please check the information you entered.",
        );
      }
      throw new Error("Action failed due to network timeout. Please try again");
    }

    return handleLogin(controller);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15_000);

    try {
      const session =
        mode === "signup"
          ? await handleSignup(controller)
          : await handleLogin(controller);
      saveSession(session, { remember });
      navigate(from?.pathname ?? "/", { replace: true, state: from?.state });
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
        <h1 className="auth-title">Learning Path</h1>
        <p className="auth-intro">
          Please enter your credentials to access your account
        </p>

        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            className={`auth-tab ${mode === "login" ? "auth-tab-active" : ""}`}
            onClick={() => switchMode("login")}
          >
            Sign In
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "signup"}
            className={`auth-tab ${mode === "signup" ? "auth-tab-active" : ""}`}
            onClick={() => switchMode("signup")}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          {mode === "signup" && (
            <>
              <label htmlFor="auth-full-name">Full name</label>
              <div className="auth-input-wrap">
                <i
                  className="bi bi-person auth-input-icon"
                  aria-hidden="true"
                ></i>
                <input
                  id="auth-full-name"
                  type="text"
                  autoComplete="name"
                  placeholder="Jane Doe"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  required
                />
              </div>
            </>
          )}

          <label htmlFor="auth-email">Email address</label>
          <div className="auth-input-wrap">
            <i
              className="bi bi-envelope auth-input-icon"
              aria-hidden="true"
            ></i>
            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              placeholder="name@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div className="auth-password-label-row">
            <label htmlFor="auth-password">Password</label>
            {mode === "login" && (
              <Link
                className="forgot-password-link"
                to="/forgot-password"
                state={{ from }}
              >
                Forgot password?
              </Link>
            )}
          </div>
          <div className="auth-input-wrap">
            <i className="bi bi-lock auth-input-icon" aria-hidden="true"></i>
            <input
              id="auth-password"
              type={showPassword ? "text" : "password"}
              autoComplete={
                mode === "signup" ? "new-password" : "current-password"
              }
              placeholder="••••••••"
              minLength={mode === "signup" ? 8 : undefined}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button
              type="button"
              className="auth-eye-toggle"
              onClick={() => setShowPassword((visible) => !visible)}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              <i
                className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`}
                aria-hidden="true"
              ></i>
            </button>
          </div>

          <label className="auth-remember-row" htmlFor="auth-remember">
            <input
              id="auth-remember"
              type="checkbox"
              checked={remember}
              onChange={(event) => setRemember(event.target.checked)}
            />
            Remember this device
          </label>

          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}

          <button className="auth-submit" type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? "Please wait…"
              : mode === "signup"
                ? "Create Account →"
                : "Sign In to Account →"}
          </button>
        </form>

        <p className="auth-switch">
          {mode === "signup" ? (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="auth-switch-link"
                onClick={() => switchMode("login")}
              >
                Sign in
              </button>
            </>
          ) : (
            <>
              Don't have an account?{" "}
              <button
                type="button"
                className="auth-switch-link"
                onClick={() => switchMode("signup")}
              >
                Create account
              </button>
            </>
          )}
        </p>

        <Link className="auth-back-link" to="/">
          ← Back to home
        </Link>
      </main>
      <Footer />
    </div>
  );
}
