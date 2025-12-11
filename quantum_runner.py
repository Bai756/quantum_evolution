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
    def __init__(self, shots=16):
        self.shots = shots
        self.sim = AerSimulator()
        parameters = [Parameter("a0"), Parameter("a1"), Parameter("a2"), Parameter("a3"), Parameter("a4"), Parameter("a5")]
        qc = QuantumCircuit(4, 2)
        qc.rx(parameters[0], 0)
        qc.ry(parameters[1], 1)
        qc.rz(parameters[2], 2)
        qc.ry(parameters[3], 3)

        qc.cx(0, 2)
        qc.cx(1, 3)
        qc.cx(2, 3)
        qc.cx(3, 0)

        qc.cry(parameters[4], 2, 0)
        qc.crx(parameters[5], 3, 1)

        qc.measure([0, 1], [0, 1])
        self.compiled = transpile(qc, self.sim)
        self.parameters = parameters

    def get_action(self, angles):
        param_bind = {
            self.parameters[0]: [angles[0]],
            self.parameters[1]: [angles[1]],
            self.parameters[2]: [angles[2]],
            self.parameters[3]: [angles[3]],
            self.parameters[4]: [angles[4]],
            self.parameters[5]: [angles[5]],
        }

        job = self.sim.run(self.compiled, parameter_binds=[param_bind], shots=self.shots)

        result = job.result()
        counts = result.get_counts()
        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        # print(sorted_items)
        mode_bitstring, mode_count = sorted_items[0]
        num = int(mode_bitstring, 2)
        return num

def test_all_angles(shots, points, batch_size):
    import itertools
    from collections import Counter

    runner = QuantumRunner(shots=shots)
    sim = runner.sim
    compiled = runner.compiled
    params = runner.parameters

    values = [k * pi / 6 for k in range(points)]
    total = points ** 6

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

    it = itertools.product(values, repeat=6)
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
    test_all_angles(32, 10, 1024)
    # run_tests(angles)
    # runner = QuantumRunner()
    # num = runner.get_action(angles)
    # print("action:", num)
