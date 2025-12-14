from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from math import pi
from collections import Counter


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

        # trainable parameters - 20 angles
        self.parameters = [Parameter(f"theta_{i}") for i in range(20)]

        qc = QuantumCircuit(5, 2)

        # Two-layer parametrized circuit over all 5 qubits
        # basically what this is doing is that it's applying RY and RZ rotations
        # to each of the 5 qubits in order and then repeating
        offset = 0
        for q in range(5):
            qc.ry(self.parameters[offset + q], q)
        offset += 5
        for q in range(5):
            qc.rz(self.parameters[offset + q], q)
        offset += 5

        # Entangling
        qc.cx(0, 3)
        qc.cx(1, 3)
        qc.cx(2, 4)
        qc.cx(3, 4)

        for q in range(5):
            qc.ry(self.parameters[offset + q], q)
        offset += 5
        for q in range(5):
            qc.rz(self.parameters[offset + q], q)

        # Measure only the action qubits q3, q4
        qc.measure([3, 4], [0, 1])

        self.qc_template = qc
        self.compiled = transpile(qc, self.sim)

    def _prepare_vision(self, qc, vision):
        # encodes vision as a basis state to make it strongly influence the circuit
        # perhaps make the vision correspond to the action qubits, that way if it's front, it will go forward ???
        front, left, right = vision
        for s, q in zip((front, left, right), (0, 1, 2)):
            # empty - |0>
            if s == 0:
                continue
            # food - |1>
            if s == 1:
                qc.x(q)
            # wall - |+>
            elif s == 2:
                qc.h(q)

    def get_action(self, angles, vision):
        if len(angles) < len(self.parameters):
            raise ValueError(f"Expected at least {len(self.parameters)} angles, got {len(angles)}")

        param_bind = {self.parameters[i]: [angles[i]] for i in range(len(self.parameters))}

        # create the circuit
        vision_qc = QuantumCircuit(5, 2)
        self._prepare_vision(vision_qc, vision)
        full_qc = vision_qc.compose(self.qc_template, inplace=False)
        compiled = transpile(full_qc, self.sim)

        job = self.sim.run(compiled, parameter_binds=[param_bind], shots=self.shots)
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


def test_all_angles(shots, points, batch_size):
    import itertools

    runner = QuantumRunner(shots=shots)
    sim = runner.sim
    compiled = runner.compiled
    params = runner.parameters

    values = [k * pi / 6 for k in range(points)]
    total = points ** len(params)

    extraordinary = []  # (angles_tuple, mode_bitstring, fraction)
    threshold = .5

    def run_batch(batch, start_idx):
        batch_len = len(batch)
        parameters = {p: [combo[idx] for combo in batch] for idx, p in enumerate(params)}

        job = sim.run(compiled, parameter_binds=[parameters], shots=shots)
        result = job.result()

        for i in range(batch_len):
            counts = result.get_counts(i)
            idx = start_idx + i + 1

            sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            top1 = sorted_items[0]
            top1_bit, top1_count = top1
            top1_frac = top1_count / float(shots)

            if len(sorted_items) > 1:
                top2 = sorted_items[1]
                top2_bit, top2_count = top2
                top2_frac = top2_count / float(shots)
            else:
                top2_bit, top2_count = "0", 0
                top2_frac = 0

            if idx % 1000 == 0:
                print(
                    f"{idx}/{total}: {batch[i]} - top1 {top1_bit} ({top1_count}/{shots}={top1_frac:.2f}), top2 {top2_bit} ({top2_count}/{shots}={top2_frac:.2f})")

            if top1_frac > threshold:
                extraordinary.append((
                    tuple(batch[i]),
                    (top1_bit, top1_count, top1_frac),
                    (top2_bit, top2_count, top2_frac),
                ))

    it = itertools.product(values, repeat=len(params))
    batch = []
    processed = 0
    for combo in it:
        batch.append(combo)
        if len(batch) >= batch_size:
            run_batch(batch, processed)
            processed += len(batch)
            batch = []
    if batch:
        run_batch(batch, processed)
        processed += len(batch)

    top1_counts = Counter(item[1][0] for item in extraordinary)
    top2_counts = Counter(item[2][0] for item in extraordinary)

    print("Top1 counts:")
    for bit, count in sorted(top1_counts.items()):
        print(f"{bit}: {count}")

    print("Top2 counts:")
    for bit, count in sorted(top2_counts.items()):
        print(f"{bit}: {count}")

    pair_counts = Counter((item[1][0], item[2][0]) for item in extraordinary)
    print("Pair counts:")
    for pair, count in pair_counts.most_common():
        print(f"{pair}: {count}")

    for angles, top1, top2 in extraordinary:
        if (top1[0], top2[0]) == ("01", "11"):
            angles_str = ", ".join(f"{a:.4f}" for a in angles)
            print(f"{angles_str}")


if __name__ == "__main__":
    angles = [0.0] * 20
    runner = QuantumRunner(shots=128)

    for vision in [(0, 0, 0), (1, 0, 0), (2, 0, 0)]:
        actions = [runner.get_action(angles, vision) for _ in range(50)]
        print(f"{vision} -", Counter(actions))
