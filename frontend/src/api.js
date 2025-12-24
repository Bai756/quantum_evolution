import axios from 'axios';

const api = axios.create({
	baseURL: "/"
});

// Export the Axios instance
export default api;

const WS_BASE = (window.location.protocol === "https:" ? "wss://" : "ws://") + window.location.host + "/ws/evolution";

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