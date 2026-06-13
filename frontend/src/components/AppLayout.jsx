import { LayoutDashboard, LogOut, SlidersHorizontal } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";

export default function AppLayout({ children }) {
  const { currentUser, logout, token } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">
          AI Crypto Advisor
        </Link>
        <nav className="topbar-actions" aria-label="Main navigation">
          {token && currentUser ? (
            <>
              <Link className="topbar-link" to="/dashboard">
                <LayoutDashboard size={17} aria-hidden="true" />
                Dashboard
              </Link>
              <Link className="topbar-link" to="/onboarding">
                <SlidersHorizontal size={17} aria-hidden="true" />
                Edit Preferences
              </Link>
              <span className="user-pill">{currentUser.name}</span>
              <button className="icon-text-button" type="button" onClick={handleLogout}>
                <LogOut size={17} aria-hidden="true" />
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </header>
      <main className="page-container">{children}</main>
    </div>
  );
}
