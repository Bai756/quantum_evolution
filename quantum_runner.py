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

if __name__ == "__main__":
    angles = (pi/2, pi/2, pi/2, pi/2, pi/2, pi/2)
    # run_tests(angles)
    # runner = QuantumRunner()
    # num = runner.get_action(angles)
    # print("action:", num)
