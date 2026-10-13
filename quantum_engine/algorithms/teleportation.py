"""
Quantum Teleportation Protocol Implementation
"""

import time
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

def build_teleportation_circuit(theta: float = 1.047, phi: float = 0.523):
    """
    Simulates genuine 3-qubit quantum teleportation:
    - Qubit 0: Alice's unknown input state |psi> = cos(theta/2)|0> + e^(i*phi)sin(theta/2)|1>
    - Qubit 1: Bell pair half (Alice)
    - Qubit 2: Bell pair half (Bob)
    """
    qc = QuantumCircuit(3, 3)

    # 1. Prepare unknown arbitrary state on q0 using U(theta, phi, 0)
    qc.u(theta, phi, 0, 0)
    qc.barrier()

    # 2. Prepare shared Bell pair between Alice (q1) and Bob (q2): (|00> + |11>)/sqrt(2)
    qc.h(1)
    qc.cx(1, 2)
    qc.barrier()

    # 3. Alice performs Bell-state measurement on q0 and q1
    qc.cx(0, 1)
    qc.h(0)
    qc.barrier()
    qc.measure(0, 0)
    qc.measure(1, 1)
    qc.barrier()

    # 4. Classical feed-forward corrections applied by Bob on q2
    # In standard teleportation: if c1=1 -> X, if c0=1 -> Z
    # Qiskit dynamic circuit syntax or classical conditioned gates:
    # Here we measure Bob's unmeasured qubit q2 into c2 after conditional gates
    with qc.if_test((qc.clbits[1], 1)):
        qc.x(2)
    with qc.if_test((qc.clbits[0], 1)):
        qc.z(2)

    # Inverse preparation to verify state fidelity (if state matches |psi>, applying U dagger brings it to |0>)
    qc.u(-theta, 0, -phi, 2)
    qc.measure(2, 2)

    return qc

def run_teleportation(theta: float = 1.047, phi: float = 0.523, shots: int = 1024, seed: int = None):
    """Executes quantum teleportation and calculates reconstructed fidelity."""
    start_time = time.perf_counter()
    qc = build_teleportation_circuit(theta, phi)

    backend = AerSimulator()
    compiled_qc = transpile(qc, backend)
    job_kwargs = {'shots': shots}
    if seed is not None:
        job_kwargs['seed_simulator'] = int(seed)

    job = backend.run(compiled_qc, **job_kwargs)
    counts = job.result().get_counts()
    if isinstance(counts, list):
        counts = counts[0]

    # Qubit 2 (leftmost bit in classical register c2 c1 c0) is measured into c[2]
    # If fidelity is 100%, c[2] must ALWAYS be '0' regardless of c[1] and c[0]
    successful_teleportations = sum(count for bitstring, count in counts.items() if bitstring[0] == '0')
    measured_fidelity = round(successful_teleportations / shots, 4)

    execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return {
        "counts": counts,
        "input_state": {
            "theta_rad": theta,
            "phi_rad": phi,
            "state_repr": f"cos({round(theta/2, 2)})|0> + e^(i*{round(phi, 2)})sin({round(theta/2, 2)})|1>"
        },
        "measured_fidelity": measured_fidelity,
        "theoretical_fidelity": 1.0,
        "explanation": "Quantum state successfully transferred using 1 shared entangled Bell pair and 2 classical bits of feed-forward communication.",
        "metrics": {
            "qubit_count": 3,
            "circuit_depth": qc.depth(),
            "gate_count": sum(qc.count_ops().values()) - qc.count_ops().get('measure', 0),
            "execution_time_ms": execution_time_ms,
            "shots": shots,
            "seed": seed,
            "backend_name": "Qiskit Aer Simulator"
        },
        "qasm": export_to_qasm(qc)
    }
