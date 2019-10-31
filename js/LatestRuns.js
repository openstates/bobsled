import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";

class LatestRuns extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      runs: [],
    };
  }

  componentDidMount() {
    fetch("/api/latest_runs")
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  render() {
    return (
      <section className="section">
        <div className="container">
          <RunList title="Latest Runs" runs={this.state.runs} />
        </div>
      </section>
    );
  }
}

export default LatestRuns;
