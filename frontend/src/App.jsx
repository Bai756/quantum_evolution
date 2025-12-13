import React, { useState } from 'react';
import './App.css';
import CreatureList from './components/Creatures.jsx';
import EvolutionControls from './components/EvolutionControls.jsx';

const App = () => {

  return (
    <div className="App">
      <header className="App-header">
        <h1>Evolution display</h1>
      </header>
      <main>
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', justifyContent: 'center' }}>
          <div style={{ width: 360 }}>
            <EvolutionControls/>
          </div>
          <div>
            <CreatureList />
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;