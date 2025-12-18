import React, {useRef, useState, useEffect} from 'react';
import {createEvolutionSocket} from '../api';

export default function EvolutionControls({ onSnapshot, onBest, gridSize, setGridSize, visionRange, setVisionRange }) {
	const [generations, setGenerations] = useState(20);
	const [children, setChildren] = useState(10);
	const [chance, setChance] = useState(0.2);
	const [repeats, setRepeats] = useState(3);
	const [elites, setElites] = useState(2);
	const [running, setRunning] = useState(false);
	const [quantum, setQuantum] = useState(true);
	const [done, setDone] = useState(false);
	const wsRef = useRef(null);

	useEffect(() => {
		// lower vision range if grid size changes
		const max = Math.max(1, Math.floor(gridSize / 2));
		if (visionRange > max) {
			setVisionRange(max);
		}
	}, [gridSize]);

	function handleRunEvolution() {
		setDone(false);
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
			grid_size: Number(gridSize || 9),
			vision_range: Number(visionRange || Math.floor(gridSize/2)),
		};
		setRunning(true);
		wsRef.current = createEvolutionSocket(payload, (msg) => {
			if (msg.error) {
				console.error('WS evolution error:', msg.error);
				setRunning(false);
				setDone(false);
			} else if (msg.best) {
				onBest(msg.best);
			} else if (msg.simulation) {
				onSnapshot(msg);
			} else if (msg.done) {
				setRunning(false);
				setDone(true);
			} else {
				// regular snapshot
				onSnapshot(msg);
			}
		}, quantum);
	}

	function handleResetSimulation() {
		if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
			return;
		}
		try {
			wsRef.current.send(JSON.stringify({ reset_simulation: true }));
		} catch (e) {
			console.error('Failed to send reset_simulation:', e);
		}
	}

	return (
		<div style={{ marginBottom: 16, textAlign: 'left' }}>
			<h3>Evolution controls</h3>

			<label>
				Mode:
				<br/>
				<select value={quantum ? 'quantum' : 'classical'} onChange={(e) => setQuantum(e.target.value === 'quantum')}>
					<option value="quantum">Quantum</option>
					<option value="classical">Classical</option>
				</select>
			</label>

			<br/>

			<label>
				Generations: {generations}
				<br/>
				<input
					type="range"
					min="1"
					max="50"
					value={generations}
					onChange={(e) => setGenerations(e.target.value)}
				/>
			</label>

			<br/>

			<label>
				Children per parent: {children}
				<br/>
				<input
					type="range"
					min="1"
					max="50"
					value={children}
					onChange={(e) => setChildren(e.target.value)}
				/>
			</label>

			<br/>

			<label>
				Mutation chance: {chance}
				<br/>
				<input
					type="range"
					min="0"
					max="1"
					step="0.01"
					value={chance}
					onChange={(e) => setChance(e.target.value)}
				/>
			</label>

			<br/>

			<label>
				Repeats (fitness average): {repeats}
				<br/>
				<input
					type="range"
					min="1"
					max="10"
					value={repeats}
					onChange={(e) => setRepeats(e.target.value)}
				/>
			</label>

			<br/>

			<label>
				Number of elites to return: {elites}
				<br/>
				<input
					type="range"
					min="1"
					max="10"
					value={elites}
					onChange={(e) => setElites(e.target.value)}
				/>
			</label>

			<br/>

			<label>
				Grid Size: {gridSize}
				<br/>
				<input type="range"
					   min="5"
					   max="15"
					   value={gridSize}
					   onChange={(e) => setGridSize(Number(e.target.value))} />
			</label>

			<br/>

			<label>
				Vision Range: {visionRange}
				<br/>
				<input type="range"
					   min="1"
					   max={Math.max(1, Math.floor(gridSize/2))}
					   value={visionRange}
					   onChange={(e) => setVisionRange(Number(e.target.value))} />
			</label>

			<div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
				<button onClick={handleRunEvolution} disabled={running}>
					{running ? 'Running...' : 'Run Evolution'}
				</button>
				{done && (
					<button onClick={handleResetSimulation}>
						Reset simulation
					</button>
				)}
			</div>
		</div>
	);
}