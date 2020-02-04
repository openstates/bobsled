export function local_websocket(path) {
  const protocol = window.location.protocol == "https:" ? "wss://" : "ws://";
  return new WebSocket(protocol + window.location.host + path);
}


export function formatTime(timeStr) {
  return timeStr.substr(0, 16).replace("T", " @ ");
}
