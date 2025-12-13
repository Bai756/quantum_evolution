import React from 'react';
import './App.css';
import CreatureList from './components/Creatures.jsx';

const App = () => {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Evolution display</h1>
      </header>
      <main>
        <CreatureList />
      </main>
    </div>
  );
};

export default App;