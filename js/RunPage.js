import React from "react";

class RunPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ws: new WebSocket(
        "ws://localhost:8000/ws/logs/" + this.props.match.params.run_id
      ),
    };
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
