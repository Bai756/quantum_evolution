import React, { useState, useEffect } from 'react';
import './App.css';
import CreatureList from './components/Creatures.jsx';
import EvolutionControls from './components/EvolutionControls.jsx';

const App = () => {
	const [snapshot, setSnapshot] = useState(null);
	const [gridSize, setGridSize] = useState(9);
	const [visionRange, setVisionRange] = useState(Math.floor(9 / 2));
	const [bestGenomeText, setBestGenomeText] = useState('');

	useEffect(() => {
		// lower visionRange if gridSize changes
		setVisionRange((prev) => {
			const max = Math.floor(gridSize / 2);
			if (prev > max) {
				return max;
			}
			return prev;
		});
	}, [gridSize]);
	
	function handleSnapshot(msg) {
		setSnapshot(msg);
	}
	function handleBest(best) {
		setSnapshot({ best });
		if (best && typeof best.genome_text === 'string') {
			setBestGenomeText(best.genome_text);
		}
	}

	return (
		<div className="App">
			<header className="App-header">
				<h1>Evolution display</h1>
			</header>
			<main>
				<div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', justifyContent: 'center' }}>
					<div style={{ width: 360 }}>
						<EvolutionControls
							gridSize={gridSize}
							setGridSize={setGridSize}
							onSnapshot={handleSnapshot}
							onBest={handleBest}
							visionRange={visionRange}
							setVisionRange={setVisionRange}
							bestGenomeText={bestGenomeText}
						/>
					</div>
					<div>
						<CreatureList snapshot={snapshot} gridSize={gridSize} />
					</div>
				</div>
			</main>
		</div>
	);
};

export default App;