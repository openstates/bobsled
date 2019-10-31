import { Link } from "react-router-dom";
import React from "react";

function RunList(props) {
  let rows = props.runs.map(run => (
    <tr key={run.uuid}>
      <td>
        <Link to={"/run/" + run.uuid}>{run.uuid}</Link>
      </td>
      {props.hideTask === "true" ? null : (
        <td>
          <Link to={"/task/" + run.task}>{run.task}</Link>
        </td>
      )}
      <td>{run.status}</td>
      <td>{run.start}</td>
      <td>{run.end}</td>
    </tr>
  ));

  return (
    <div className="column">
      <h3 className="title is-3">{props.title}</h3>
      <table className="table">
        <thead>
          <tr>
            <th>UUID</th>
            {props.hideTask === "true" ? null : <th>Task</th>}
            <th>Status</th>
            <th>Start</th>
            <th>End</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  );
}

export default RunList;
