from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from math import pi

def run_tests():
    qc = QuantumCircuit(2)
    qc.ry(2*pi/3, 0)
    qc.rx(2*pi/3, 1)
    qc.cx(0, 1)
    qc.h(0)
    qc.measure_all()

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
        a = Parameter("a")
        b = Parameter("b")
        qc = QuantumCircuit(2)
        qc.ry(a, 0)
        qc.rx(b, 1)
        qc.cx(0, 1)
        qc.h(0)
        qc.measure_all()
        self.compiled = transpile(qc, self.sim)
        self.a = a
        self.b = b

    def get_action(self, a, b):
        job = self.sim.run([self.compiled], parameter_binds=[{self.a: [a], self.b: [b]}], shots=self.shots)
        result = job.result()
        counts = result.get_counts()

        sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        sorted_dict = dict(sorted_items)
        mode_bitstring, mode_count = sorted_items[0]
        num = int(mode_bitstring, 2)
        return num

if __name__ == "__main__":
    # run_tests()
    runner = QuantumRunner()
    num = runner.get_action(pi/2, pi/2)