// import { initializeApp } from "firebase/app";
// import { getAuth } from "firebase/auth";
// import { getFirebaseConfig } from "../config/firebase";

// // Load config from env
// const firebaseConfig = getFirebaseConfig();

// // Initialize Firebase
// const app = initializeApp(firebaseConfig);

// // Initialize Auth
// const auth = getAuth(app);

// // Optional: set language automatically
// auth.useDeviceLanguage();

// export { app, auth };


import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirebaseConfig } from "../config/firebase";

const firebaseConfig = getFirebaseConfig();

let app = null;
let auth = null;

// Only initialize Firebase if API key exists
if (firebaseConfig.apiKey) {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  auth.useDeviceLanguage();
} else {
  console.warn("Firebase not configured. Auth disabled.");
}

export { app, auth };