import React from "react";
import { createRoot } from "react-dom/client";
import CloudDashboard from "./CloudDashboard.jsx";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element #root was not found.");
}

createRoot(rootElement).render(
  <React.StrictMode>
    <CloudDashboard />
  </React.StrictMode>
);
