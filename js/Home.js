import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";
import { local_websocket, formatTime, enabledColumn } from "./utils.js";

const STATUS = {
  Pending: { color: "#aaa", icon: "\u23F3" }, // gray, hourglass start
  Running: { color: "#add8e6", icon: "\u2699" }, // blue, gear
  Error: { color: "#db4c40", icon: "\u2716" }, // red, X
  Success: { color: "#89bd9e", icon: "\u2714" }, // green, check
  UserKilled: { color: "#f0c987", icon: "\u26a0" }, // yellow, warning
  TimedOut: { color: "#8b1e3f", icon: "\u231b" }, // magenta, hourglass done
  Missing: { color: "#3c153b", icon: "\u2754" }, // purple, question
};

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
    this.state.ws.onmessage = (evt) => {
      const message = JSON.parse(evt.data);
      this.setState({ beatStatus: this.state.beatStatus + "\n" + message.msg });
    };

    fetch("/api/index")
      .then((response) => response.json())
      .then((data) => this.setState(data));
  }

  renderTaskStatus(task) {
    if (!task.latest_run) {
      return (
        <>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
        </>
      );
    } else {
      const statusColumns = task.recent_statuses.slice(1, 4).map((s, i) => (
        <td key={i} style={{ background: STATUS[s].color }}>
          {STATUS[s].icon}
        </td>
      ));
      return (
        <>
          <td style={{ background: STATUS[task.latest_run.status].color }}>
            <Link to={"/run/" + task.latest_run.uuid}>
              {task.latest_run.status} - {formatTime(task.latest_run.start)}
            </Link>
          </td>
          {statusColumns}
        </>
      );
    }
  }

  render() {
    let rows = this.state.tasks.map((task) => {
      return (
        <tr key={task.name}>
          <td>
            <Link to={"/task/" + task.name}>{task.name}</Link>
          </td>
          {enabledColumn(task.enabled)}
          {this.renderTaskStatus(task)}
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
                <th>Enabled</th>
                <th>Latest Run</th>
                <th colSpan={3}>Recently</th>
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
