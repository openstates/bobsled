import React from "react";
import { Link } from "react-router-dom";

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
    let rows = this.state.runs.map(run => (
      <tr key={run.uuid}>
        <td>
          <Link to={"/run/" + run.uuid}>{run.uuid}</Link>
        </td>
        <td>{run.status}</td>
        <td>{run.start}</td>
        <td>{run.end}</td>
      </tr>
    ));
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
                    <th>Entrypoint</th>
                    <td>{this.state.task.entrypoint}</td>
                  </tr>
                  <tr>
                    <th>Memory</th>
                    <td>{this.state.task.memory}</td>
                  </tr>
                  <tr>
                    <th>Tags</th>
                    <td>{this.state.task.tags}</td>
                  </tr>
                  <tr>
                    <th>Enabled</th>
                    <td>{this.state.task.enabled ? "yes" : "no"}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="column">
              <h3 className="title is-3">Recent Runs</h3>
              <table className="table">
                <thead>
                  <tr>
                    <th>UUID</th>
                    <th>Status</th>
                    <th>Start</th>
                    <th>End</th>
                  </tr>
                </thead>
                <tbody>{rows}</tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    );
  }
}

export default TaskPage;
