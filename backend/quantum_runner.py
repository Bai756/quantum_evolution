from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from math import pi


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

        # trainable parameters: 2 layers * 5 qubits * (RY,RZ) = 20
        self.parameters = [Parameter(f"theta_{i}") for i in range(20)]
        # vision parameters for front, left, right
        self.vision_parameters = [Parameter("v_front"), Parameter("v_left"), Parameter("v_right")]

        qc = QuantumCircuit(5, 2)

        # Encode vision on input qubits q0, q1, q2
        qc.ry(self.vision_parameters[0], 0)
        qc.ry(self.vision_parameters[1], 1)
        qc.ry(self.vision_parameters[2], 2)

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

        self.compiled = transpile(qc, self.sim)

    def _encode_vision_angles(self, vision):
        # turns vision (0,1,2) into angles (-pi/3,0,pi/3)
        v_scale = pi / 3.0
        front, left, right = vision
        encoded = []
        for s in (front, left, right):
            code = int(s) - 1
            encoded.append(code * v_scale)
        return encoded

    def get_action(self, angles, vision):
        if len(angles) < len(self.parameters):
            raise ValueError(f"Expected at least {len(self.parameters)} angles, got {len(angles)}")

        v_front, v_left, v_right = self._encode_vision_angles(vision)

        param_bind = {
            # trainable angles
            **{self.parameters[i]: [angles[i]] for i in range(len(self.parameters))},
            self.vision_parameters[0]: [v_front],
            self.vision_parameters[1]: [v_left],
            self.vision_parameters[2]: [v_right],
        }

        job = self.sim.run(self.compiled, parameter_binds=[param_bind], shots=self.shots)
        result = job.result()
        counts = result.get_counts()

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        mode_bitstring, _ = sorted_items[0]

        mapping = {
            "00": 0,
            "01": 1,
            "10": 2,
            "11": 3,
        }
        return mapping.get(mode_bitstring, 0)


def test_all_angles(shots, points, batch_size):
    import itertools
    from collections import Counter

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
    runner = QuantumRunner()
    # print(runner.compiled)
    action = runner.get_action(angles, vision=(0, 0, 0))
    print("action:", action)
