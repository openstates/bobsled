import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";
import { local_websocket, formatTime, enabledColumn } from "./utils.js";

const COLORS = {
  Pending: "#aaa",        // gray
  Running: '#add8e6',     // blue
  Error: '#db4c40',       // red
  Success: '#89bd9e',     // green
  UserKilled: '#f0c987',  // yellow
  TimedOut: '#8b1e3f',    // magenta
  Missing: '#3c153b',     // purple
}

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

  renderTaskStatus(task) {
    if (!task.latest_run) {
      return <>
        <td></td><td></td>
      </>;
    } else {
      const statusColors = task.recent_statuses.map(s => COLORS[s]);
      var backgroundStr = `repeating-linear-gradient(90deg,
          ${statusColors[1]}, ${statusColors[1]} 33%,
          ${statusColors[2]} 33%, ${statusColors[2]} 66%,
          ${statusColors[3]} 66%, ${statusColors[3]}`;
      return <>
        <td 
          style={{background: statusColors[0]}}
        >
          <Link to={"/run/" + task.latest_run.uuid}>
            {task.latest_run.status} - {formatTime(task.latest_run.start)}
          </Link>
        </td>
        <td style={{background: backgroundStr, "border-left-width": "1px"}}>
          &nbsp;
        </td>
        </>;
    }
  }

  render() {
    let rows = this.state.tasks.map(task => {
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
                <th>Recently</th>
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
