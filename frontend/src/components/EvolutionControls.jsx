import React, {useRef, useState, useEffect} from 'react';
import {createEvolutionSocket} from '../api';

function downloadTextFile(text, filename) {
	const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	a.remove();
	URL.revokeObjectURL(url);
}

export default function EvolutionControls({ onSnapshot, onBest, gridSize, setGridSize, visionRange, setVisionRange, bestGenomeText, showVisuals, setShowVisuals }) {
	const [generations, setGenerations] = useState(20);
	const [children, setChildren] = useState(10);
	const [chance, setChance] = useState(0.2);
	const [repeats, setRepeats] = useState(3);
	const [elites, setElites] = useState(2);
	const [running, setRunning] = useState(false);
	const [quantum, setQuantum] = useState(true);
	const [done, setDone] = useState(false);
	const [maxMoves, setMaxMoves] = useState(5);
	const [wallDensity, setWallDensity] = useState(0.0);
	const [sigma, setSigma] = useState(3);
	const [genomeText, setGenomeText] = useState('');
	const [genomeError, setGenomeError] = useState('');
	const [isGenomeDragOver, setIsGenomeDragOver] = useState(false);
	const wsRef = useRef(null);
	const genomeFileInputRef = useRef(null);

	useEffect(() => {
		// lower vision range if grid size changes
		const max = Math.max(1, Math.floor(gridSize / 2));
		if (visionRange > max) {
			setVisionRange(max);
		}
		// limit max moves size
		if (maxMoves > gridSize) {
			setMaxMoves(gridSize);
		}
	}, [gridSize]);

	function handleRunEvolution() {
		// clear any displayed best visualization when starting a new run
		try {
			window.dispatchEvent(new CustomEvent('clearBestVisualization'));
		} catch (e) {
			// ignore
		}
		setGenomeError('');
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
			sigma: Number(sigma),
			repeats: Number(repeats),
			elites: Number(elites),
			grid_size: Number(gridSize),
			vision_range: Number(visionRange || Math.floor(gridSize/2)),
			max_moves: Number(maxMoves),
			wall_density: Number(wallDensity),
			visualize: showVisuals,
		};
		setRunning(true);
		wsRef.current = createEvolutionSocket(payload, (msg) => {
			if (msg.error) {
				console.error('WS evolution error:', msg.error);
				setGenomeError(String(msg.error));
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

	async function handleCopyBestGenome() {
		setGenomeError('');
		try {
			if (!bestGenomeText) {
				setGenomeError('No best genome yet. Run evolution first.');
				return;
			}
			await navigator.clipboard.writeText(bestGenomeText);
		} catch (e) {
			console.error('Failed to copy genome:', e);
			setGenomeError('Failed to copy genome to clipboard.');
		}
	}

	function handleDownloadBestGenome() {
		setGenomeError('');
		if (!bestGenomeText) {
			setGenomeError('No best genome yet. Run evolution first.');
			return;
		}
		const mode = quantum ? 'quantum' : 'classical';
		downloadTextFile(bestGenomeText, `best_${mode}_genome.txt`);
	}

	function handleLoadBestIntoTextbox() {
		setGenomeError('');
		if (!bestGenomeText) {
			setGenomeError('No best genome yet. Run evolution first.');
			return;
		}
		setGenomeText(bestGenomeText);
	}

	function handleRunPastedGenome() {
		setGenomeError('');
		setDone(false);
		// close previous stream if any
		if (wsRef.current) {
			try { wsRef.current.close(); } catch (_) {}
			wsRef.current = null;
		}
		const payload = {
			run_genome: true,
			genome_text: String(genomeText),
			grid_size: Number(gridSize),
			vision_range: Number(visionRange || Math.floor(gridSize/2)),
			max_moves: Number(maxMoves),
			wall_density: Number(wallDensity),
			visualize: showVisuals,
		};
		setRunning(true);

		wsRef.current = createEvolutionSocket(payload, (msg) => {
			if (msg.error) {
				console.error('WS genome run error:', msg.error);
				setGenomeError(String(msg.error));
				setRunning(false);
				setDone(false);
			} else if (msg.best) {
				onBest(msg.best);
			} else if (msg.simulation) {
				onSnapshot(msg);
			} else {
				// ignore
			}
		}, quantum);
	}

	async function loadGenomeFromFile(file) {
		try {
			setGenomeError('');
			const content = await file.text();
			setGenomeText(String(content ?? ''));
		} catch (e) {
			console.error('Failed to read genome file:', e);
			setGenomeError('Failed to read file.');
		} finally {
			if (genomeFileInputRef.current) {
				genomeFileInputRef.current.value = '';
			}
		}
	}

	function handleGenomeDrop(e) {
		e.preventDefault();
		e.stopPropagation();
		setIsGenomeDragOver(false);
		const file = e.dataTransfer?.files?.[0];
		if (file) {
			loadGenomeFromFile(file);
		}
	}

	return (
		<div style={{ marginBottom: 16, textAlign: 'left' }}>
			<h3>Evolution controls</h3>

			<label>
				Mode:
				<br/>
				<select value={quantum ? 'quantum' : 'classical'} onChange={(e) => {
					// set default value of sigma based on if quantum or classical
					const isQuantum = e.target.value === 'quantum';
					setQuantum(isQuantum);
					setSigma(isQuantum ? 3 : 0.2);
				}}>
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
				Chance of mutation: {chance}
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
				Mutation magnitude: {sigma}
				<br/>
				<input
					type="range"
					min="0"
					max={quantum ? "12" : "1"}
					step={quantum ? "0.1" : "0.01"}
					value={sigma}
					onChange={(e) => setSigma(e.target.value)}
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

			<br/>

			<label>
				Wall density: {wallDensity}
				<br/>
				<input type="range"
					   min="0"
					   max="0.5"
					   step="0.01"
					   value={wallDensity}
					   onChange={(e) => setWallDensity(Number(e.target.value))} />
			</label>

			<br/>

			<label>
				Energy: {maxMoves}
				<br/>
				<input type="range"
					   min="1"
					   max={Math.max(1, gridSize)}
					   value={maxMoves}
					   onChange={(e) => setMaxMoves(Number(e.target.value))} />
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

			<hr style={{ margin: '16px 0' }} />
			<div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
				<label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
					<input type="checkbox" checked={showVisuals} onChange={(e) => setShowVisuals(e.target.checked)} />
					<span>Show visualization</span>
				</label>
			</div>

			<h4>Genome</h4>
			<div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
				<button onClick={handleCopyBestGenome} disabled={!bestGenomeText}>Copy genome</button>
				<button onClick={handleDownloadBestGenome} disabled={!bestGenomeText}>Download genome</button>
				<button onClick={handleLoadBestIntoTextbox} disabled={!bestGenomeText}>Load best into textbox</button>
				<button onClick={() => genomeFileInputRef.current?.click()}>Upload genome file</button>
				<input
					type="file"
					ref={genomeFileInputRef}
					accept=".txt,text/plain"
					style={{ display: 'none' }}
					onChange={(e) => loadGenomeFromFile(e.target.files?.[0])}
				/>
			</div>

			<div
				style={{
					marginTop: 8,
					padding: 6,
					borderRadius: 8,
					border: isGenomeDragOver ? '2px dashed #646cff' : '1px solid rgba(127,127,127,0.35)',
					background: isGenomeDragOver ? 'rgba(100,108,255,0.08)' : 'transparent',
				}}
				onDragEnter={(e) => {
					e.preventDefault();
					e.stopPropagation();
					setIsGenomeDragOver(true);
				}}
				onDragOver={(e) => {
					e.preventDefault();
					e.stopPropagation();
					setIsGenomeDragOver(true);
				}}
				onDragLeave={(e) => {
					e.preventDefault();
					e.stopPropagation();
					setIsGenomeDragOver(false);
				}}
				onDrop={handleGenomeDrop}
			>
				<textarea
					rows={8}
					style={{ width: '100%', fontFamily: 'monospace' }}
					placeholder={'Paste / drop a genome text file here...'}
					value={genomeText}
					onChange={(e) => setGenomeText(e.target.value)}
				/>
			</div>

			<div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
				<button onClick={handleRunPastedGenome} disabled={!genomeText}>Run pasted genome</button>
			</div>

			{genomeError && (
				<div style={{ marginTop: 8, color: 'crimson', whiteSpace: 'pre-wrap' }}>
					{genomeError}
				</div>
			)}
		</div>
	);
}