/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useState, useEffect, useCallback } from "react";
import { authService } from "../services/authService";
import {
  signInWithGooglePopup,
  signInWithGoogleRedirect,
  getGoogleRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChange
} from "../firebase/auth";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [authMethod, setAuthMethod] = useState("email");

  useEffect(() => {
    const token = localStorage.getItem("token");
    const savedMethod = localStorage.getItem("authMethod");

    if (token) {
      setAuthMethod(savedMethod || "email");
      fetchUser();
    } else {
      checkGoogleRedirect();
    }
  }, []);

  const checkGoogleRedirect = async () => {
    try {
      const result = await getGoogleRedirectResult();

      if (result) {
        await handleGoogleSignInResult(result);
      } else {
        const unsubscribe = onAuthStateChange(async (firebaseUser) => {
          if (firebaseUser) {
            const idToken = await firebaseUser.getIdToken(true);
            await signInWithFirebaseToken(idToken, firebaseUser);
          } else {
            setLoading(false);
          }
          unsubscribe();
        });
      }
    } catch (err) {
      console.error("Redirect check failed:", err);
      setLoading(false);
    }
  };

  const fetchUser = async () => {
    try {
      const userData = await authService.getMe();
      setUser(userData);
    } catch {
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      setError(null);
      const data = await authService.login(email, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("authMethod", "email");
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
      throw err;
    }
  };

  const register = async (email, username, password) => {
    try {
      setError(null);
      const data = await authService.register(email, username, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("authMethod", "email");
      setUser(data.user);
      return data;
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
      throw err;
    }
  };

  const loginWithGoogle = async (useRedirect = false) => {
    try {
      setError(null);

      if (useRedirect) {
        await signInWithGoogleRedirect();
        return;
      }

      const result = await signInWithGooglePopup();
      await handleGoogleSignInResult(result);
      return result;
    } catch (err) {
      setError(err.message || "Google sign-in failed");
      throw err;
    }
  };

  const handleGoogleSignInResult = async (result) => {
    try {
      const { user, idToken, isNewUser } = result;

      const userData = await authService.loginWithGoogle({
        id_token: idToken,
        user_info: {
          uid: user.uid,
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
          emailVerified: user.emailVerified,
          isNewUser,
          provider: "google"
        }
      });

      localStorage.setItem("token", userData.access_token);
      localStorage.setItem("refreshToken", userData.refresh_token || "");
      localStorage.setItem("authMethod", "google");

      setAuthMethod("google");
      setUser(userData.user);

      return userData;
    } catch (err) {
      console.error("Backend Google login failed:", err);
      setError(err.response?.data?.detail || "Google authentication failed");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signInWithFirebaseToken = async (idToken, firebaseUser) => {
    try {
      const userData = await authService.loginWithGoogle({
        id_token: idToken,
        user_info: {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: firebaseUser.displayName,
          photoURL: firebaseUser.photoURL,
          emailVerified: firebaseUser.emailVerified,
          provider: "google"
        }
      });

      localStorage.setItem("token", userData.access_token);
      localStorage.setItem("authMethod", "google");

      setAuthMethod("google");
      setUser(userData.user);
    } catch (err) {
      console.error("Backend Firebase token login failed:", err);
      await firebaseSignOut();
      setError(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const logout = useCallback(async () => {
    try {
      if (authMethod === "google") {
        await firebaseSignOut();
      }

      localStorage.removeItem("token");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("authMethod");

      setUser(null);
      setAuthMethod("email");
    } catch (err) {
      console.error("Logout error:", err);

      localStorage.removeItem("token");
      localStorage.removeItem("authMethod");

      setUser(null);
      setAuthMethod("email");
    }
  }, [authMethod]);

  const value = {
    user,
    loading,
    error,
    login,
    register,
    loginWithGoogle,
    logout,
    authMethod,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
