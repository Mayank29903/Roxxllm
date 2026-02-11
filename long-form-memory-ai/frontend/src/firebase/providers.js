import { GoogleAuthProvider } from "firebase/auth";

const googleProvider = new GoogleAuthProvider();

// Optional: force account selection
googleProvider.setCustomParameters({
  prompt: "select_account"
});

export { googleProvider };
