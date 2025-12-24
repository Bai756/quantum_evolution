# Quantum Evolution

This is a small experimental environment for evolving agents that search a grid for food. It includes two controllers (a quantum circuit and a classical neural-network), an environment simulator, evolution/training scripts, and a React frontend for live visualization.

It's a playground to run evolutionary optimization (generations, mutation, selection) against a simple grid world where creatures have limited energy, can turn and move, and can eat food to gain energy.

Hosted at: https://quantumevolution.me

## Host locally

Requirements
- Python 3.12 (I used 3.12.12)
- Node.js and npm

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Start the backend:

```bash
cd backend
python main.py
```

Go to: `0.0.0.0:8000` in your browser to access the frontend.


## Files
- backend/
    - environment.py - the grid world, Creature model, movement, energy, and sight logic.
    - simulate.py - quantum evolution helpers and a simple pygame renderer for debugging.
    - simulate_classical.py - classical evolution helpers.
    - quantum_runner.py / classical_runner.py - controller implementations that map observations to actions.
    - web_helpers.py - async helpers used by the WebSocket endpoint (simulation loop, async evolution generators, serialization helpers).
    - main.py - FastAPI app. It uses a websocket endpoint for evolution and live visualization.
- frontend/
    - a small React app that connects to the backend via websocket and displays the currently best creature and a live simulation view.
    - Notable files (I want to show off because it's really cool and was hard to make):
        - src/components/CircuitView.jsx — renders a quantum circuit visually using SVG
        - src/components/NerualNetView.jsx — renders the neural network visually using SVG

## About the environment
- The environment is a simple 2D grid where each cell can be empty, contain food, a wall, or a creature.
- Creatures have limited energy that depletes when they move forward.
- Creatures can sense their environment using a simple vision system that detects food in three directions (left, front, right).
    - The vision is normalized to values between -1 and 1 based on the distance to the nearest food in each direction. Food is positive, empty space is zero, and walls are negative.
    - E.g. if vision was 5 blocks, food is 1 cell away in front, 3 cells away to the left, and there's a wall 2 cell to the right, the vision would be [0.4, 1.0, -0.8].
- Creatures can perform 4 actions: nothing, move forward, turn left, turn right.

## About the controllers
### Quantum Circuit
- The quantum circuit is a 7 qubit parameterized circuit.
- The first 3 qubits are used to encode the creature's vision (left, front, right).
    - Vision values are mapped to rotation angles for Rx gates.
    - Rx gates directly change the qubit state from 0 to 1 based on the angle.
    - -1 maps to 0 radians (|0⟩ state), 0 maps to π/2 (superposition), and 1 maps to π (|1⟩ state), and values in between.
- The next 2 qubits are used as ancilla qubits to increase the circuit's expressibility.
- The circuit uses rotation gates (Ry, Rz) to encode the observations and entanglement (CNOT) gates to create correlations between qubits.
    - There are 20 trainable rotation angle parameters in total.
- Finally, the last 2 qubits are measured and the results are used to determine the creature's action (nothing, turn left, move forward, turn right).
    - (00: nothing, 01: move forward, 10: turn left, 11: turn right)
    - Actions are calculated based on the expected value of the measured qubits.

### Neural Network
- The neural network is a simple feedforward network with two hidden layers.
- Input layer: 3 nodes (vision inputs)
- Hidden layer 1: 32 nodes
- Hidden layer 2: 16 nodes
- Output layer: 4 nodes
- No activation functions are used for simplicity.
- Actions are determined by taking the argmax of the output layer.

## Notes
These are just some things to keep in mind:
- Since tensorflow is not supported on raspberry pi, I rewrote it using only numpy for a simple neural network implementation.
- Please note that if you use high parameter values (e.g. large children number and large elites to return), it may take a really long time to complete.
- The quantum runner uses a simple parameterized quantum circuit with rotation and entanglement gates. It uses the `qiskit` library for simulation.
    - Now, I'm not going to explain quantum computing here, but if you're interested in learning more about it, here's the wiki page https://en.wikipedia.org/wiki/Quantum_computing. Read about qubits and operations.
- This grid environment is very simplified and the creature senses are also basic. Creatures only have vision that extend a certain number of cells forward, to the left, and to the right.
    - This means that often, the quantum circuit can perform better than the neural network because it inherently more randomly so it can explore the environment better.
    - I'm sure if the environment was more complex with more sensors, hazards, etc. the neural network would outperform the quantum circuit.
- Sometimes the NN can get stuck in training, not improving, so just rerun it if that happens.
