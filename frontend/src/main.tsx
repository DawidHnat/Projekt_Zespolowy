import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource-variable/inter";
import { App } from "./app/App";
import "./app/styles.css";
import "./app/dashboard-editor.css";
import "./app/glass.css";
import "./app/backgrounds.css";
import "./app/workspace-pages.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
