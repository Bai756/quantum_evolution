from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import matplotlib.pyplot as plt
from math import pi
from environment import *

a = pi/2
b = pi/2

qc = QuantumCircuit(3)
qc.ry(a, 0)
qc.rx(b, 1)
qc.cx(0, 1)
qc.h(0)
qc.h(2)
qc.measure_all()

sim = AerSimulator()
compiled = transpile(qc, sim)
job = sim.run(compiled, shots=1024)
result = job.result()
counts = result.get_counts()

sorted_items = sorted(counts.items())
sorted_dict = dict(sorted_items)
labels, values = sorted_dict.keys(), sorted_dict.values()

# plt.bar(labels, values)
# plt.show()