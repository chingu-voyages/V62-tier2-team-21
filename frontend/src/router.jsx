import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import HomePage from "./pages/HomePage";
import FormPage from "./pages/FormPage";
import LearningPathPage from "./pages/LearningPathPage";
import ErrorPage from "./pages/ErrorPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: App,
    errorElement: <ErrorPage />,
    children: [
      { index: true, Component: HomePage, id: "home" },
      { path: "form", Component: FormPage, id: "form" },
      {
        path: "learning-path",
        Component: LearningPathPage,
        id: "learning-path",
      },
    ],
  },
]);
