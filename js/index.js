import ReactDOM from "react-dom";
import React from "react";
import App from "./App";

window.addEventListener("load", () => {
  const app = document.querySelector('[data-hook="app"]');
  if (app) {
    ReactDOM.render(
      React.createElement(App, {
      }),
      app
    );
  }
});
