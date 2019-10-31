import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";
import { local_websocket } from "./utils.js";

class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tasks: [],
      runs: [],
      ws: local_websocket("/ws/beat"),
      beatStatus: "...",
    };
  }

  componentDidMount() {
    this.state.ws.onmessage = evt => {
      const message = JSON.parse(evt.data);
      this.setState({ beatStatus: this.state.beatStatus + "\n" + message.msg });
    };

    fetch("/api/index")
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  renderRunStatus(run) {
    if (!run) {
      return "";
    } else {
      return (
        <Link to={"/run/" + run.uuid}>
          {run.status} at {run.start.substr(0, 16)}
        </Link>
      );
    }
  }

  render() {
    let rows = this.state.tasks.map(task => {
      return (
        <tr key={task.name}>
          <td>
            <Link to={"/task/" + task.name}>{task.name}</Link>
          </td>
          <td>{task.tags}</td>
          <td>{task.enabled ? "yes" : "no"}</td>
          <td>{this.renderRunStatus(task.latest_run)}</td>
        </tr>
      );
    });

    return (
      <section className="section">
        <div className="container">
          <table className="table">
            <thead>
              <tr>
                <th>Task</th>
                <th>Tags</th>
                <th>Enabled</th>
                <th>Latest Run</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>

          <RunList title="Currently Running" runs={this.state.runs} />

          <div>
            <h3 className="title is-3">Beat Status</h3>
            <pre>{this.state.beatStatus}</pre>
          </div>
        </div>
      </section>
    );
  }
}

export default Home;
