import React from "react";

class RunPage extends React.Component {
  constructor(props) {
    super(props);
    const protocol = window.location.protocol == "https:" ? "wss://" : "ws://"
    this.state = {
      ws: new WebSocket(
        protocol + window.location.host + "/ws/logs/" + this.props.match.params.run_id
      ),
    };
    this.stopRun = this.stopRun.bind(this);
  }

  stopRun() {
    const outerThis = this;
    fetch("/api/run/" + this.props.match.params.run_id + "/stop")
      .then(response => response.json())
      .then(function(data) {});
  }

  componentDidMount() {
    this.state.ws.onmessage = evt => {
      const message = JSON.parse(evt.data);
      this.setState(message);
    };

    fetch("/api/run/" + this.props.match.params.run_id)
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  render() {
    return (
      <section className="section">
        <div className="container">
          <h1 className="title is-2">
            {this.state.task}: {this.state.uuid}
          </h1>

          {this.state.status == "Running" ? (
            <a className="button is-danger is-centered" onClick={this.stopRun}>
              Stop
            </a>
          ) : (
            ""
          )}

          <table className="table">
            <tbody>
              <tr>
                <th>Status</th>
                <td>{this.state.status}</td>
              </tr>
              <tr>
                <th>Start</th>
                <td>{this.state.start}</td>
              </tr>
              <tr>
                <th>Exit Code</th>
                <td>{this.state.exit_code}</td>
              </tr>
            </tbody>
          </table>

          <pre>{this.state.logs}</pre>
        </div>
      </section>
    );
  }
}

export default RunPage;
