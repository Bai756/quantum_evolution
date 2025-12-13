import React, { useState } from 'react';
import api from '../api';

export default function EvolutionControls({ onResult }) {
  const [generations, setGenerations] = useState(20);
  const [children, setChildren] = useState(10);
  const [chance, setChance] = useState(0.2);
  const [repeats, setRepeats] = useState(3);
  const [elites, setElites] = useState(2);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);

  async function handleStart() {
    setRunning(true);
    setResult(null);
    try {
      const payload = {
        generations: Number(generations),
        children: Number(children),
        chance: Number(chance),
        repeats: Number(repeats),
        elites: Number(elites),
      };
      const resp = await api.post('/run_evolution', payload);
      const elitesResult = resp.data.elites;
      console.log('Evolution finished, elites:', elitesResult);
      setResult(elitesResult);
      if (typeof onResult === 'function') {
        onResult(elitesResult);
      }
    } catch (err) {
      console.error('run_evolution failed', err);
      setResult(null);
    } finally {
      setRunning(false);
    }
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

      <div style={{ marginTop: 12 }}>
        <button onClick={handleStart} disabled={running}>
          {running ? 'Running...' : 'Start Evolution'}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: 12 }}>
          <h4>Elites returned:</h4>
          <pre style={{ textAlign: 'left', whiteSpace: 'pre-wrap' }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

