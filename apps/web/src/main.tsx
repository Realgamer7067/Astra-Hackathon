import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app/App";
import "./style.css";

const root = document.getElementById("root");
if (!root) throw new Error("Application mount is missing.");
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
