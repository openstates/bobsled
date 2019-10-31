import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";

class TaskPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      task_name: this.props.match.params.task_name,
      task: {},
      runs: [],
    };
    this.startRun = this.startRun.bind(this);
  }

  componentDidMount() {
    fetch("/api/task/" + this.state.task_name)
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  startRun() {
    const outerThis = this;
    fetch("/api/task/" + this.state.task_name + "/run")
      .then(response => response.json())
      .then(function(data) {
        let runs = outerThis.state.runs;
        runs.unshift(data);
        outerThis.setState({ runs: runs });
      });
  }

  render() {
    return (
      <section className="section">
        <div className="container">
          <h1 className="title is-2"> {this.state.task.name} </h1>

          <div className="columns">
            <div className="column is-one-quarter">
              <a
                className="button is-primary is-centered"
                onClick={this.startRun}
              >
                Start Run
              </a>

              <table className="table">
                <tbody>
                  <tr>
                    <th>Image</th>
                    <td>{this.state.task.image}</td>
                  </tr>
                  <tr>
                    <th>Tags</th>
                    <td>{this.state.task.tags}</td>
                  </tr>
                  <tr>
                    <th>Entrypoint</th>
                    <td>{this.state.task.entrypoint}</td>
                  </tr>
                  <tr>
                    <th>Environment</th>
                    <td>{this.state.task.environment}</td>
                  </tr>
                  <tr>
                    <th>Memory</th>
                    <td>{this.state.task.memory}</td>
                  </tr>
                  <tr>
                    <th>CPU</th>
                    <td>{this.state.task.cpu}</td>
                  </tr>
                  <tr>
                    <th>Timeout</th>
                    <td>
                      {this.state.task.timeout
                        ? this.state.task.timeout
                        : "none"}
                    </td>
                  </tr>
                  <tr>
                    <th>Enabled</th>
                    <td>{this.state.task.enabled ? "yes" : "no"}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <RunList title="Recent Runs" runs={this.state.runs} hideTask="true" />
          </div>
        </div>
      </section>
    );
  }
}

export default TaskPage;
