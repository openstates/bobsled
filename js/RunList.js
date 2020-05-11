import { Link } from "react-router-dom";
import React from "react";
import { formatTime } from "./utils.js";

function statusCol(status) {
  if (status === "Success") {
    return <td className="success">Success</td>;
  } else if (status === "Error") {
    return <td className="error">Error</td>;
  } else {
    return <td>{status}</td>;
  }
}

function RunList(props) {
  let rows = props.runs.map(run => (
    <tr key={run.uuid}>
      <td>
        <Link to={"/run/" + run.uuid}>{formatTime(run.start)}</Link>
      </td>
      {props.hideTask === "true" ? null : (
        <td>
          <Link to={"/task/" + run.task}>{run.task}</Link>
        </td>
      )}
      {statusCol(run.status)}
      <td>{formatTime(run.end)}</td>
      <td>{run.duration}</td>
    </tr>
  ));

  return (
    <div className="column">
      <h3 className="title is-3">{props.title}</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Start Time</th>
            {props.hideTask === "true" ? null : <th>Task</th>}
            <th>Status</th>
            <th>End Time</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  );
}

export default RunList;
