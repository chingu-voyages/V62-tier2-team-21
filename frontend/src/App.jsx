import { Outlet } from "react-router-dom";
import "./App.css";
import Header from "./components/layout/Header";

function App() {
  return (
    <div className="app-shell">
      <Header />
      <Outlet />
    </div>
  );
}

export default App;
