import {
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  getAdditionalUserInfo
} from "firebase/auth";

import { auth } from "./init";
import { googleProvider } from "./providers";

// Popup login
export const signInWithGooglePopup = async () => {
  try {
    const result = await signInWithPopup(auth, googleProvider);

    const user = result.user;
    const idToken = await user.getIdToken();
    const additionalInfo = getAdditionalUserInfo(result);

    return {
      idToken,
      user: {
        uid: user.uid,
        email: user.email,
        name: user.displayName,
        photo: user.photoURL,
        isNewUser: additionalInfo?.isNewUser || false
      }
    };
  } catch (error) {
    console.error("Google sign-in error:", error);
    throw error;
  }
};

// Redirect login (recommended for production)
export const signInWithGoogleRedirect = async () => {
  try {
    await signInWithRedirect(auth, googleProvider);
  } catch (error) {
    console.error("Redirect sign-in error:", error);
    throw error;
  }
};

// Handle redirect result
export const getGoogleRedirectResult = async () => {
  try {
    const result = await getRedirectResult(auth);

    if (!result) return null;

    const user = result.user;
    const idToken = await user.getIdToken();
    const additionalInfo = getAdditionalUserInfo(result);

    return {
      idToken,
      user: {
        uid: user.uid,
        email: user.email,
        name: user.displayName,
        photo: user.photoURL,
        isNewUser: additionalInfo?.isNewUser || false
      }
    };
  } catch (error) {
    console.error("Redirect result error:", error);
    throw error;
  }
};

// Logout
export const signOut = async () => {
  try {
    await firebaseSignOut(auth);
  } catch (error) {
    console.error("Sign-out error:", error);
    throw error;
  }
};

// Listen to auth state changes
export const onAuthStateChange = (callback) => {
  return onAuthStateChanged(auth, callback);
};

// Get current user
export const getCurrentUser = () => {
  return auth.currentUser;
};

// Get Firebase ID token (for backend)
export const getIdToken = async (user = null) => {
  const currentUser = user || auth.currentUser;
  if (!currentUser) return null;

  return await currentUser.getIdToken();
};
