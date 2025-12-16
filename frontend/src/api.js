import axios from 'axios';

// change this later
const api = axios.create({
	baseURL: "http://localhost:8000"
});

// Export the Axios instance
export default api;

// change this later
const WS_BASE = 'ws://localhost:8000/ws/evolution';

export function createEvolutionSocket(params, onMessage, quantum = true) {
	const url = `${WS_BASE}?quantum=${quantum ? 'true' : 'false'}`;
	const socket = new WebSocket(url);

	socket.onopen = () => {
		socket.send(JSON.stringify(params));
	};

	socket.onmessage = (e) => {
		try {
			const msg = JSON.parse(e.data);
			if (onMessage){
				onMessage(msg);
			}
		} catch (_) {
			// ignore
		}
	};

	// ignore errors and close
	socket.onerror = () => {};

	socket.onclose = () => {};

	return socket;
}