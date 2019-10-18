import React from "react";
import { Link } from "react-router-dom";
import RunList from "./RunList.js";

function local_websocket(path) {
  const protocol = window.location.protocol == "https:" ? "wss://" : "ws://";
  return new WebSocket(protocol + window.location.host + path);
}

class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tasks: [],
      runs: [],
      ws: local_websocket("/ws/beat")
    };
  }

  componentDidMount() {
    this.state.ws.onmessage = evt => {
      const message = JSON.parse(evt.data);
      console.log(message);
    };

    fetch("/api/index")
      .then(response => response.json())
      .then(data => this.setState(data));
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
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>

          <RunList title="Currently Running" runs={this.state.runs} />
        </div>
      </section>
    );
  }
}

export default Home;
