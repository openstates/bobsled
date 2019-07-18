import React from "react";

class RunPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  componentDidMount() {
    fetch("/api/run/" + this.props.match.params.run_id)
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  render() {
    return (
      <section className="section">
        <div className="container">
          <h1 className="title is-2">
            {" "}
            {this.state.task}: {this.state.uuid}{" "}
          </h1>

          <pre>{this.state.logs}</pre>
        </div>
      </section>
    );
  }
}

export default RunPage;
