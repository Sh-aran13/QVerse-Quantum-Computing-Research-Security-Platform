"""
Quantum Fourier Transform (QFT) and Inverse QFT Implementation
"""

import math
import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

def build_qft_circuit(num_qubits: int, inverse: bool = False, input_state: int = 1):
    """
    Constructs an authentic QFT or Inverse QFT circuit for a configurable number of qubits.
    """
    if num_qubits < 1 or num_qubits > 6:
        raise ValueError("Number of qubits for QFT must be between 1 and 6.")

    qc = QuantumCircuit(num_qubits, num_qubits)

    # Initialize input computational state if specified (e.g. state |1> -> X on q0)
    for q in range(num_qubits):
        if (input_state >> q) & 1:
            qc.x(q)

    # Sub-circuit for QFT
    def apply_qft(circuit, n):
        for i in range(n):
            circuit.h(i)
            for j in range(i + 1, n):
                angle = math.pi / (2 ** (j - i))
                circuit.cp(angle, j, i)
        # Swap qubits to adhere to standard binary endianness
        for i in range(n // 2):
            circuit.swap(i, n - i - 1)

    qft_sub = QuantumCircuit(num_qubits, name="QFT")
    apply_qft(qft_sub, num_qubits)

    if inverse:
        qft_gate = qft_sub.inverse()
        qc.append(qft_gate, range(num_qubits))
    else:
        qc.append(qft_sub, range(num_qubits))

    qc.measure(range(num_qubits), range(num_qubits))
    return qc

def run_qft(num_qubits: int = 3, inverse: bool = False, input_state: int = 1, shots: int = 1024, seed: int = None):
    """Executes QFT on local Qiskit Aer simulator."""
    start_time = time.perf_counter()
    qc = build_qft_circuit(num_qubits, inverse, input_state)

    backend = AerSimulator()
    compiled_qc = transpile(qc, backend)
    job_kwargs = {'shots': shots}
    if seed is not None:
        job_kwargs['seed_simulator'] = int(seed)

    job = backend.run(compiled_qc, **job_kwargs)
    counts = job.result().get_counts()
    if isinstance(counts, list):
        counts = counts[0]

    probabilities = {k: v / shots for k, v in counts.items()}
    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "counts": counts,
        "probabilities": probabilities,
        "num_qubits": num_qubits,
        "input_state": input_state,
        "is_inverse": inverse,
        "metrics": {
            "qubit_count": num_qubits,
            "circuit_depth": qc.depth(),
            "gate_count": sum(qc.count_ops().values()) - qc.count_ops().get('measure', 0),
            "execution_time_ms": execution_time_ms,
            "shots": shots,
            "seed": seed,
            "backend_name": "Qiskit Aer Simulator"
        },
        "qasm": export_to_qasm(qc)
    }
