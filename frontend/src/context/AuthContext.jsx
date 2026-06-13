import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser } from "../api/authApi.js";
import { clearStoredToken, getStoredToken, setStoredToken } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getStoredToken());
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(Boolean(getStoredToken()));

  async function loadCurrentUser() {
    if (!getStoredToken()) {
      setCurrentUser(null);
      setIsLoading(false);
      return null;
    }

    setIsLoading(true);

    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
      return user;
    } catch {
      clearStoredToken();
      setToken(null);
      setCurrentUser(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }

  async function login(credentials) {
    const tokenResponse = await loginUser(credentials);
    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    return loadCurrentUser();
  }

  function logout() {
    clearStoredToken();
    setToken(null);
    setCurrentUser(null);
  }

  useEffect(() => {
    loadCurrentUser();
  }, []);

  const value = useMemo(
    () => ({
      token,
      currentUser,
      isLoading,
      login,
      logout,
      loadCurrentUser,
      refreshCurrentUser: loadCurrentUser,
    }),
    [token, currentUser, isLoading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
