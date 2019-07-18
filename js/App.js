import React from "react";
import { BrowserRouter as Router, Route, Link } from "react-router-dom";


function App() {
  return (
    <Router>
      <Route exact path="/" component={Home} />
      <Route path="/task/:task_name" component={TaskPage} />
    </Router>
  );
}


class Home extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      tasks: []
    };
  }

  componentDidMount() {
    fetch("/api/index")
      .then(response => response.json())
      .then(data => this.setState(data));
  }

  render() {
    let rows = this.state.tasks.map(task => {
      return (<tr key={task.name}>

        <td><Link to={ "/task/" + task.name }>{ task.name }</Link></td>
        <td>{ task.tags }</td>
        <td>{ task.enabled ? "yes" : "no" }</td>
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
      <tbody>
        { rows }
      </tbody>
      </table>

      </div>
      </section>
    )
  }
}

class TaskPage extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      task_name: this.props.match.params.task_name,
      task: {},
      runs: []
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
    fetch("/api/run/" + this.state.task_name)
      .then(response => response.json())
      .then(function(data) {
        let runs = outerThis.state.runs;
        runs.unshift(data);
        outerThis.setState({runs: runs});
      });
  }

  render() {
    let rows = this.state.runs.map(run =>
      <tr key={ run.uuid }>
        <td>{ run.uuid }</td>
        <td>{ run.status }</td>
        <td>{ run.start }</td>
        <td>{ run.end }</td>
      </tr>
    );
    return (
    <section className="section">
    <div className="container">

      <h1 className="title is-2"> { this.state.task.name } </h1>

      <div className="columns">

      <div className="column is-one-quarter">

        <a className="button is-primary is-centered" onClick={this.startRun}>
          Start Run
        </a>

        <table className="table">
        <tbody>
        <tr>
          <th>Image</th>
          <td>{ this.state.task.image }</td>
        </tr>
        <tr>
          <th>Entrypoint</th>
          <td>{ this.state.task.entrypoint }</td>
        </tr>
        <tr>
          <th>Memory</th>
          <td>{ this.state.task.memory }</td>
        </tr>
        <tr>
          <th>Tags</th>
          <td>{ this.state.task.tags }</td>
        </tr>
        <tr>
          <th>Enabled</th>
          <td>{ this.state.task.enabled ? "yes" : "no" }</td>
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
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>

      </div>
    </div>
    </section>
    );
  }
}

function Header() {
  return (
    <ul>
      <li>
        <Link to="/">Home</Link>
      </li>
      <li>
        <Link to="/about">About</Link>
      </li>
      <li>
        <Link to="/topics">Topics</Link>
      </li>
    </ul>
  );
}

export default App;
