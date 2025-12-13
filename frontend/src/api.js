import axios from 'axios';

// change this later
const api = axios.create({
  baseURL: "http://localhost:8000"
});

// Export the Axios instance
export default api;

// change this later
const WS_URL = 'ws://localhost:8000/ws/evolution';

export function createEvolutionSocket(params, onMessage) {
  const socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    socket.send(JSON.stringify(params));
  };

  socket.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data);
      if (onMessage) onMessage(msg);
    } catch (_) {
      // ignore
    }
  };

  // ignore errors and close
  socket.onerror = () => {};

  socket.onclose = () => {};

  return socket;
}