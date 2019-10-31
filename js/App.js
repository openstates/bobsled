import React from "react";
import { BrowserRouter as Router, Route, Link } from "react-router-dom";
import RunPage from "./RunPage";
import LatestRuns from "./LatestRuns";
import Home from "./Home";
import TaskPage from "./TaskPage";

function App() {
  return (
    <Router>
      <Route exact path="/" component={Home} />
      <Route exact path="/latest_runs" component={LatestRuns} />
      <Route path="/task/:task_name" component={TaskPage} />
      <Route path="/run/:run_id" component={RunPage} />
    </Router>
  );
}

export default App;
