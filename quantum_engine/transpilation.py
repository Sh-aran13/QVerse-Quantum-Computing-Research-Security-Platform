"""
Quantum Circuit Optimization & Transpilation Engine
Applies genuine Qiskit transpilation passes and optimization levels (0-3).
"""

import time
from qiskit import transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import build_qiskit_circuit, export_to_qasm, validate_circuit_definition

SUPPORTED_BASIS_GATES = [
    ['id', 'rz', 'sx', 'x', 'cx'],  # Standard IBM Quantum Basis
    ['u1', 'u2', 'u3', 'cx'],       # Standard Universal Single-qubit + CNOT
    ['rx', 'ry', 'rz', 'cz']        # Neutral atom / alternative architecture
]

def analyze_circuit_structure(definition):
    """Computes comprehensive structural metrics for an input circuit."""
    validate_circuit_definition(definition)
    qc = build_qiskit_circuit(definition)
    
    ops = qc.count_ops()
    total_gates = sum(ops.values()) - ops.get('measure', 0)
    
    return {
        "num_qubits": qc.num_qubits,
        "circuit_depth": qc.depth(),
        "total_gates": total_gates,
        "gate_breakdown": {k: v for k, v in ops.items() if k != 'measure'},
        "num_measurements": ops.get('measure', 0),
        "qasm": export_to_qasm(qc)
    }

def optimize_quantum_circuit(definition, optimization_level: int = 2, basis_gates: list = None):
    """
    Applies genuine multi-pass Qiskit transpilation and circuit optimization.
    Optimization levels:
    0: No optimization (direct mapping)
    1: Light optimization (adjacent gate cancellation)
    2: Medium optimization (commutative analysis & gate reduction)
    3: Heavy optimization (unitary synthesis & CX optimization)
    """
    if optimization_level not in [0, 1, 2, 3]:
        raise ValueError("Optimization level must be an integer between 0 and 3.")

    validate_circuit_definition(definition)
    qc = build_qiskit_circuit(definition)
    
    original_metrics = {
        "qubit_count": qc.num_qubits,
        "circuit_depth": qc.depth(),
        "gate_count": sum(qc.count_ops().values()) - qc.count_ops().get('measure', 0),
        "gate_breakdown": {k: v for k, v in qc.count_ops().items() if k != 'measure'}
    }

    start_time = time.perf_counter()
    backend = AerSimulator()

    target_basis = basis_gates if basis_gates else ['id', 'rz', 'sx', 'x', 'cx']
    optimized_qc = transpile(
        qc,
        backend=backend,
        optimization_level=optimization_level,
        basis_gates=target_basis
    )
    optimization_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    opt_ops = optimized_qc.count_ops()
    optimized_metrics = {
        "qubit_count": optimized_qc.num_qubits,
        "circuit_depth": optimized_qc.depth(),
        "gate_count": sum(opt_ops.values()) - opt_ops.get('measure', 0),
        "gate_breakdown": {k: v for k, v in opt_ops.items() if k != 'measure'},
        "cx_count": opt_ops.get('cx', 0)
    }

    depth_reduction = original_metrics["circuit_depth"] - optimized_metrics["circuit_depth"]
    depth_reduction_pct = round((depth_reduction / max(1, original_metrics["circuit_depth"])) * 100, 1)

    gate_reduction = original_metrics["gate_count"] - optimized_metrics["gate_count"]

    return {
        "original_metrics": original_metrics,
        "optimized_metrics": optimized_metrics,
        "comparison": {
            "depth_reduction": depth_reduction,
            "depth_reduction_pct": depth_reduction_pct,
            "gate_reduction": gate_reduction,
            "optimization_level": optimization_level,
            "basis_gates": target_basis,
            "optimization_time_ms": optimization_time_ms
        },
        "original_qasm": export_to_qasm(qc),
        "optimized_qasm": export_to_qasm(optimized_qc)
    }
