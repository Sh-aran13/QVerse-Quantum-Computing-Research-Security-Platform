"""
Grover's Search Algorithm Implementation
"""

import math
import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

def build_grover_circuit(marked_state: str, num_iterations: int = None):
    """
    Constructs a genuine Grover search circuit for a binary marked state (e.g., '10' or '101').
    """
    n = len(marked_state)
    if n < 2 or n > 5:
        raise ValueError("Search space must be between 2 and 5 qubits for local simulation.")

    if not all(c in ('0', '1') for c in marked_state):
        raise ValueError("Marked state must be a valid binary bitstring.")

    # Optimal iterations: floor(pi/4 * sqrt(2^n))
    N = 2 ** n
    optimal_iterations = max(1, int(math.floor((math.pi / 4.0) * math.sqrt(N))))
    iterations = num_iterations if (num_iterations is not None and num_iterations > 0) else optimal_iterations

    qc = QuantumCircuit(n, n)

    # Step 1: Initialize equal superposition
    for q in range(n):
        qc.h(q)

    # Step 2: Grover Iteration (Oracle + Diffusion)
    for _ in range(iterations):
        # --- Oracle Phase Inversion for marked_state ---
        # Qiskit qubit indexing: qubit 0 is rightmost bit (little-endian)
        for i, bit in enumerate(reversed(marked_state)):
            if bit == '0':
                qc.x(i)

        # Multi-controlled Z gate using H - MCX - H on target
        if n == 2:
            qc.cz(0, 1)
        else:
            qc.h(n - 1)
            qc.mcx(list(range(n - 1)), n - 1)
            qc.h(n - 1)

        for i, bit in enumerate(reversed(marked_state)):
            if bit == '0':
                qc.x(i)

        # --- Diffusion Operator (Inversion about the mean: 2|s><s| - I) ---
        for q in range(n):
            qc.h(q)
            qc.x(q)

        if n == 2:
            qc.cz(0, 1)
        else:
            qc.h(n - 1)
            qc.mcx(list(range(n - 1)), n - 1)
            qc.h(n - 1)

        for q in range(n):
            qc.x(q)
            qc.h(q)

    # Step 3: Measurement
    qc.measure(range(n), range(n))
    return qc, iterations, optimal_iterations

def run_grover_search(marked_state: str, shots: int = 1024, iterations: int = None, seed: int = None):
    """Executes Grover's search on Qiskit Aer simulator."""
    start_time = time.perf_counter()
    qc, actual_iterations, optimal_iterations = build_grover_circuit(marked_state, iterations)

    backend = AerSimulator()
    compiled_qc = transpile(qc, backend)
    job_kwargs = {'shots': shots}
    if seed is not None:
        job_kwargs['seed_simulator'] = int(seed)

    job = backend.run(compiled_qc, **job_kwargs)
    result = job.result()
    counts = result.get_counts()
    if isinstance(counts, list):
        counts = counts[0]

    marked_counts = counts.get(marked_state, 0)
    measured_probability = marked_counts / shots
    theoretical_probability = math.sin((2 * actual_iterations + 1) * math.asin(1.0 / math.sqrt(2 ** len(marked_state)))) ** 2

    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "counts": counts,
        "probabilities": {k: v / shots for k, v in counts.items()},
        "marked_state": marked_state,
        "search_space_size": 2 ** len(marked_state),
        "iterations": actual_iterations,
        "optimal_iterations": optimal_iterations,
        "measured_success_probability": round(measured_probability, 4),
        "theoretical_success_probability": round(theoretical_probability, 4),
        "metrics": {
            "qubit_count": qc.num_qubits,
            "circuit_depth": qc.depth(),
            "gate_count": sum(qc.count_ops().values()) - qc.count_ops().get('measure', 0),
            "execution_time_ms": execution_time_ms,
            "shots": shots,
            "seed": seed,
            "backend_name": "Qiskit Aer Simulator"
        },
        "qasm": export_to_qasm(qc)
    }
