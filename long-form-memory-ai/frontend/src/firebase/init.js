import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirebaseConfig } from "../config/firebase";

// Load config from env
const firebaseConfig = getFirebaseConfig();

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Auth
const auth = getAuth(app);

// Optional: set language automatically
auth.useDeviceLanguage();

export { app, auth };
