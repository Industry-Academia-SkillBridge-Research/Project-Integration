import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { initializeConfig } from "@/services/configService";

// Initialize configuration from config server on app startup
initializeConfig().then(() => {
  createRoot(document.getElementById("root")!).render(<App />);
}).catch((error) => {
  console.error('Failed to initialize config, using fallbacks:', error);
  // Still render the app with fallback configuration
  createRoot(document.getElementById("root")!).render(<App />);
});
