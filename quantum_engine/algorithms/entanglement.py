"""
Quantum Entanglement Lab: Bell States and GHZ States
"""

import time
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

SUPPORTED_STATES = {
    'phi_plus': {'qubits': 2, 'formula': '(|00> + |11>)/sqrt(2)', 'desc': 'Bell State Phi+'},
    'phi_minus': {'qubits': 2, 'formula': '(|00> - |11>)/sqrt(2)', 'desc': 'Bell State Phi-'},
    'psi_plus': {'qubits': 2, 'formula': '(|01> + |10>)/sqrt(2)', 'desc': 'Bell State Psi+'},
    'psi_minus': {'qubits': 2, 'formula': '(|01> - |10>)/sqrt(2)', 'desc': 'Bell State Psi-'},
    'ghz': {'qubits': 3, 'formula': '(|000> + |111>)/sqrt(2)', 'desc': 'Greenberger–Horne–Zeilinger (GHZ) Tripartite Entangled State'}
}

def build_entanglement_circuit(state_type: str = 'phi_plus'):
    if state_type not in SUPPORTED_STATES:
        raise ValueError(f"Unknown state type '{state_type}'. Choose from {list(SUPPORTED_STATES.keys())}")

    if state_type.startswith('phi_') or state_type.startswith('psi_'):
        qc = QuantumCircuit(2, 2)
        if state_type == 'phi_plus':
            qc.h(0)
            qc.cx(0, 1)
        elif state_type == 'phi_minus':
            qc.x(0)
            qc.h(0)
            qc.cx(0, 1)
        elif state_type == 'psi_plus':
            qc.x(1)
            qc.h(0)
            qc.cx(0, 1)
        elif state_type == 'psi_minus':
            qc.x(0)
            qc.x(1)
            qc.h(0)
            qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        return qc
    elif state_type == 'ghz':
        qc = QuantumCircuit(3, 3)
        qc.h(0)
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.measure([0, 1, 2], [0, 1, 2])
        return qc

def run_entanglement_experiment(state_type: str = 'phi_plus', shots: int = 1024, seed: int = None):
    start_time = time.perf_counter()
    qc = build_entanglement_circuit(state_type)

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
    spec = SUPPORTED_STATES[state_type]

    return {
        "counts": counts,
        "probabilities": probabilities,
        "state_type": state_type,
        "formula": spec['formula'],
        "description": spec['desc'],
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
