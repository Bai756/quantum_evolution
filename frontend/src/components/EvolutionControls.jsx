import React, {useRef, useState} from 'react';
import {createEvolutionSocket} from '../api';

export default function EvolutionControls({ onSnapshot, onBest }) {
	const [generations, setGenerations] = useState(20);
	const [children, setChildren] = useState(10);
	const [chance, setChance] = useState(0.2);
	const [repeats, setRepeats] = useState(3);
	const [elites, setElites] = useState(2);
	const [running, setRunning] = useState(false);
	const wsRef = useRef(null);

	function handleRunEvolution() {
		// close previous stream if any
		if (wsRef.current) {
			try { wsRef.current.close(); } catch (_) {}
			wsRef.current = null;
		}
		const payload = {
			generations: Number(generations),
			children: Number(children),
			chance: Number(chance),
			repeats: Number(repeats),
			elites: Number(elites),
		};
		setRunning(true);
		wsRef.current = createEvolutionSocket(payload, (msg) => {
			if (msg.error) {
				console.error('WS evolution error:', msg.error);
				setRunning(false);
			} else if (msg.done && msg.best) {
				// optional intermediate done=false best was sent previously
			} else if (msg.best) {
				onBest(msg.best);
			} else if (msg.simulation) {
				onSnapshot(msg);
			} else if (msg.done) {
				setRunning(false);
			} else {
				// regular snapshot
				console.log(msg)
				onSnapshot(msg);
			}
		});
	}

	return (
		<div style={{ marginBottom: 16, textAlign: 'left' }}>
			<h3>Evolution controls</h3>

			<label>
				Generations: {generations}
				<br />
				<input
					type="range"
					min="1"
					max="50"
					value={generations}
					onChange={(e) => setGenerations(e.target.value)}
				/>
			</label>

			<br />

			<label>
				Children per parent: {children}
				<br />
				<input
					type="range"
					min="1"
					max="50"
					value={children}
					onChange={(e) => setChildren(e.target.value)}
				/>
			</label>

			<br />

			<label>
				Mutation chance: {chance}
				<br />
				<input
					type="range"
					min="0"
					max="1"
					step="0.01"
					value={chance}
					onChange={(e) => setChance(e.target.value)}
				/>
			</label>

			<br />

			<label>
				Repeats (fitness average): {repeats}
				<br />
				<input
					type="range"
					min="1"
					max="10"
					value={repeats}
					onChange={(e) => setRepeats(e.target.value)}
				/>
			</label>

			<br />

			<label>
				Number of elites to return: {elites}
				<br />
				<input
					type="range"
					min="1"
					max="10"
					value={elites}
					onChange={(e) => setElites(e.target.value)}
				/>
			</label>

			<div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
				<button onClick={handleRunEvolution} disabled={running}>
					{running ? 'Running...' : 'Run Evolution'}
				</button>
			</div>
		</div>
	);
}