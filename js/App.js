import React from "react";
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import RunPage from "./RunPage";
import Home from "./Home";
import TaskPage from "./TaskPage";

function App() {
  return (
    <Router>
      <Route exact path="/" component={Home} />
      <Route path="/task/:task_name" component={TaskPage} />
      <Route path="/run/:run_id" component={RunPage} />
    </Router>
  );
}

export default App;
