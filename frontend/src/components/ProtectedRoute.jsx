import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext.jsx";
import LoadingMessage from "./LoadingMessage.jsx";

export default function ProtectedRoute({ children }) {
  const { isLoading, token } = useAuth();

  if (isLoading) {
    return <LoadingMessage message="Checking your session..." />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
