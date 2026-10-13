"""
Quantum Circuit Simulator Interface using Qiskit Aer
"""

import time
import numpy as np
from qiskit_aer import AerSimulator
from qiskit import transpile
from qiskit.quantum_info import Statevector

from .circuit_builder import build_qiskit_circuit, export_to_qasm

class CircuitSimulator:
    def __init__(self, backend_name='aer_simulator'):
        self.backend_name = backend_name
        self.backend = AerSimulator()

    def simulate(self, definition, shots=1024, seed=None, include_statevector=False):
        """
        Executes a validated circuit definition on local Qiskit Aer simulator.
        Returns authentic measurement counts, probabilities, circuit metrics, and optional statevector.
        """
        start_time = time.perf_counter()

        # Build genuine Qiskit circuit
        qc = build_qiskit_circuit(definition)
        qubit_count = qc.num_qubits
        circuit_depth = qc.depth()
        gate_count = sum(qc.count_ops().values()) - qc.count_ops().get('measure', 0)

        # Transpile for Aer backend
        compiled_circuit = transpile(qc, self.backend)

        # Run shot-based simulation
        job_kwargs = {'shots': shots}
        if seed is not None:
            job_kwargs['seed_simulator'] = int(seed)

        job = self.backend.run(compiled_circuit, **job_kwargs)
        result = job.result()
        counts = result.get_counts()

        # If counts is a list (e.g. multi-experiment), grab the first dict
        if isinstance(counts, list):
            counts = counts[0]

        # Calculate empirical probabilities
        total_shots = sum(counts.values()) if counts else shots
        probabilities = {bitstring: count / total_shots for bitstring, count in counts.items()}

        statevector_data = None
        # Compute exact statevector only for circuits with <= 10 qubits without mid-circuit collapse if requested
        if include_statevector and qubit_count <= 10:
            try:
                # Remove measurement operations to obtain pure statevector
                qc_no_measure = qc.remove_final_measurements(inplace=False)
                sv = Statevector.from_instruction(qc_no_measure)
                # Convert complex numbers to serializable dicts
                statevector_data = [
                    {"real": float(val.real), "imag": float(val.imag), "prob": float(abs(val)**2)}
                    for val in sv.data
                ]
            except Exception:
                statevector_data = None

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        qasm_str = export_to_qasm(qc)

        return {
            "counts": counts,
            "probabilities": probabilities,
            "metrics": {
                "qubit_count": qubit_count,
                "circuit_depth": circuit_depth,
                "gate_count": gate_count,
                "execution_time_ms": execution_time_ms,
                "shots": shots,
                "seed": seed,
                "backend_name": "Qiskit Aer Simulator",
                "backend_version": "0.17.2",
            },
            "statevector": statevector_data,
            "qasm": qasm_str
        }
