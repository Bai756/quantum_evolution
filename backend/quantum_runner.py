from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from math import pi
from collections import Counter
import random


def run_tests(angles):
    qc = QuantumCircuit(4, 2)
    qc.rx(angles[0], 0)
    qc.ry(angles[1], 1)
    qc.rz(angles[2], 2)
    qc.ry(angles[3], 3)

    qc.cx(0, 2)
    qc.cx(1, 3)
    qc.cx(2, 3)
    qc.cx(3, 0)

    qc.cry(angles[4], 2, 0)
    qc.crx(angles[5], 3, 1)

    qc.measure([0, 1], [0, 1])
    print(qc)

    sim = AerSimulator()
    compiled = transpile(qc, sim)
    job = sim.run(compiled, shots=1024)
    result = job.result()
    counts = result.get_counts()

    sorted_items = sorted(counts.items())
    sorted_dict = dict(sorted_items)
    labels, values = sorted_dict.keys(), sorted_dict.values()

    plt.bar(labels, values)
    plt.show()


class QuantumRunner:
    def __init__(self, shots=32):
        self.shots = shots
        self.sim = AerSimulator()

        self.parameters = [Parameter(f"theta_{i}") for i in range(20)]

        qc = QuantumCircuit(7, 2)
        # q0–2: vision
        # q3–4: latent
        # q5–6: action

        # 0-2 controls to latent qubit 3
        qc.cry(self.parameters[0], 0, 3)
        qc.cry(self.parameters[1], 1, 3)
        qc.cry(self.parameters[2], 2, 3)

        # 3-5 controls to latent qubit 4
        qc.cry(self.parameters[3], 0, 4)
        qc.cry(self.parameters[4], 1, 4)
        qc.cry(self.parameters[5], 2, 4)

        # 6-9 rotations on latent qubits
        qc.ry(self.parameters[6], 3)
        qc.rz(self.parameters[7], 3)
        qc.ry(self.parameters[8], 4)
        qc.rz(self.parameters[9], 4)

        # entangling between the two latent qubits
        qc.cx(3, 4)
        qc.cx(4, 3)

        # more rotations on latent qubits
        qc.ry(self.parameters[10], 3)
        qc.rz(self.parameters[11], 3)
        qc.ry(self.parameters[12], 4)
        qc.rz(self.parameters[13], 4)

        # entanglement between q3 and q4
        qc.cx(3, 4)
        qc.cx(4, 3)

        # Rotations from latent qubits (q3,q4) into action qubits (q5,q6)
        qc.cry(self.parameters[14], 3, 5)
        qc.cry(self.parameters[15], 4, 6)

        # This is not necessary. just temporarily here because if not it doesn't work
        qc.cx(0, 5)
        qc.cx(1, 6)
        qc.cx(2, 6)

        # Final rotations on the action qubits before measurement
        qc.ry(self.parameters[16], 5)
        qc.ry(self.parameters[17], 6)
        qc.rz(self.parameters[18], 5)
        qc.rz(self.parameters[19], 6)

        # Measure only the action qubits (q5,q6)
        qc.measure([5, 6], [0, 1])

        self.qc_template = qc

    def _prepare_vision(self, qc, vision):
        # encodes vision as a basis state to make it strongly influence the circuit
        front, left, right = vision
        for i, s in enumerate((front, left, right)):
            # rotation of the x, maybe keep this?
            # qc.rx((pi / 2) * s, i)

            # initialize a state directly based on s
            # if s >= 0:
            #     theta = pi * s
            #     state = [math.cos(theta / 2), math.sin(theta / 2)]
            #     qc.initialize(state, i)

            # -1 is 0, 0 is pi/2, 1 is pi scale
            theta = (pi / 2) * (s + 1)
            qc.rx(theta, i)

    def get_action(self, angles, vision):
        if len(angles) < len(self.parameters):
            raise ValueError(f"Expected at least {len(self.parameters)} angles, got {len(angles)}")

        param_bind = {self.parameters[i]: [angles[i]] for i in range(len(self.parameters))}

        # create the circuit
        vision_qc = QuantumCircuit(7, 2)
        self._prepare_vision(vision_qc, vision)
        full_qc = vision_qc.compose(self.qc_template, inplace=False)

        job = self.sim.run(full_qc, parameter_binds=[param_bind], shots=self.shots)
        result = job.result()
        counts = result.get_counts()

        # Compute expected action value from the distribution
        total_shots = sum(counts.values()) or 1
        p00 = counts.get("00", 0) / total_shots
        p01 = counts.get("01", 0) / total_shots
        p10 = counts.get("10", 0) / total_shots
        p11 = counts.get("11", 0) / total_shots

        expected = p00 * 0 + p01 * 1 + p10 * 2 + p11 * 3
        action = int(round(expected))
        if action < 0:
            action = 0
        elif action > 3:
            action = 3
        return action

def serialize_circuit(angles, vision=None):
    # round params to 2 decimals
    def r(x):
        return float(round(float(x), 2))

    gates = []
    idx = 0

    # vision - rx gates on qubits 0-2
    if vision is not None:
        for i, s in enumerate(vision):
            theta = (pi / 2) * (s + 1)
            gates.append({"type": "rx", "targets": [i], "param": r(theta), "index": idx})
            idx += 1
    else:
        for i in range(3):
            gates.append({"type": "rx", "targets": [i], "param": "v", "index": idx})
            idx += 1

    # Just following the circuit structure
    for p in range(0, 3):
        gates.append({"type": "cry", "controls": [p], "targets": [3], "param": r(angles[p]), "index": idx})
        idx += 1

    for p in range(3, 6):
        gates.append({"type": "cry", "controls": [p - 3], "targets": [4], "param": r(angles[p]), "index": idx})
        idx += 1

    gates.append({"type": "ry", "targets": [3], "param": r(angles[6]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [3], "param": r(angles[7]), "index": idx}); idx += 1
    gates.append({"type": "ry", "targets": [4], "param": r(angles[8]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [4], "param": r(angles[9]), "index": idx}); idx += 1

    gates.append({"type": "cx", "controls": [3], "targets": [4], "index": idx}); idx += 1
    gates.append({"type": "cx", "controls": [4], "targets": [3], "index": idx}); idx += 1

    gates.append({"type": "ry", "targets": [3], "param": r(angles[10]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [3], "param": r(angles[11]), "index": idx}); idx += 1
    gates.append({"type": "ry", "targets": [4], "param": r(angles[12]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [4], "param": r(angles[13]), "index": idx}); idx += 1

    gates.append({"type": "cx", "controls": [3], "targets": [4], "index": idx}); idx += 1
    gates.append({"type": "cx", "controls": [4], "targets": [3], "index": idx}); idx += 1

    gates.append({"type": "cry", "controls": [3], "targets": [5], "param": r(angles[14]), "index": idx}); idx += 1
    gates.append({"type": "cry", "controls": [4], "targets": [6], "param": r(angles[15]), "index": idx}); idx += 1

    gates.append({"type": "cx", "controls": [0], "targets": [5], "index": idx}); idx += 1
    gates.append({"type": "cx", "controls": [1], "targets": [6], "index": idx}); idx += 1
    gates.append({"type": "cx", "controls": [2], "targets": [6], "index": idx}); idx += 1

    gates.append({"type": "ry", "targets": [5], "param": r(angles[16]), "index": idx}); idx += 1
    gates.append({"type": "ry", "targets": [6], "param": r(angles[17]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [5], "param": r(angles[18]), "index": idx}); idx += 1
    gates.append({"type": "rz", "targets": [6], "param": r(angles[19]), "index": idx}); idx += 1

    gates.append({"type": "measure", "targets": [5, 6], "index": idx})

    return {"qubits": 7, "gates": gates}


if __name__ == "__main__":
    angles = [random.uniform(-12*pi, 12*pi) for _ in range(20)]
    runner = QuantumRunner()
    print(serialize_circuit(angles))

    # for vision in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, 0, 1), (0, 1, 1), (2, 2, 2)]:
    #     actions = [runner.get_action(angles, vision) for _ in range(100)]
    #     print(f"{vision} -", Counter(actions))
