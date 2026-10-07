import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import HomePage from "./pages/HomePage";
import FormPage from "./pages/FormPage";
import LearningPathPage from "./pages/LearningPathPage";
import SavedLearningPathsPage from "./pages/SavedLearningPathsPage";
import ManageAccountPage from "./pages/ManageAccountPage";
import AuthPage from "./pages/AuthPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ErrorPage from "./pages/ErrorPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    errorElement: <ErrorPage />,
    children: [
      { index: true, Component: HomePage, id: "home" },
      { path: "form", Component: FormPage, id: "form" },
      { path: "login", Component: AuthPage, id: "login" },
      { path: "signup", Component: AuthPage, id: "signup" },
      {
        path: "forgot-password",
        Component: ForgotPasswordPage,
        id: "forgot-password",
      },
      {
        path: "learning-path",
        Component: LearningPathPage,
        id: "learning-path",
      },
      {
        path: "saved-learning-paths",
        Component: SavedLearningPathsPage,
        id: "saved-learning-paths",
      },
      {
        path: "account",
        Component: ManageAccountPage,
        id: "account",
      },
    ],
  },
]);
