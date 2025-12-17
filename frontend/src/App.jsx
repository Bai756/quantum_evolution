import React, { useState } from 'react';
import './App.css';
import CreatureList from './components/Creatures.jsx';
import EvolutionControls from './components/EvolutionControls.jsx';

const App = () => {
	const [snapshot, setSnapshot] = useState(null);
	const [gridSize, setGridSize] = useState(9);

	function handleSnapshot(msg) {
		setSnapshot(msg);
	}
	function handleBest(best) {
		setSnapshot({ best });
	}

	return (
		<div className="App">
			<header className="App-header">
				<h1>Evolution display</h1>
			</header>
			<main>
				<div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', justifyContent: 'center' }}>
					<div style={{ width: 360 }}>
						<EvolutionControls gridSize={gridSize} setGridSize={setGridSize} onSnapshot={handleSnapshot} onBest={handleBest}/>
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