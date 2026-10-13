"""
Circuit Builder & Validator for QVerse Quantum Engine
"""

import math
from qiskit import QuantumCircuit
from qiskit.qasm2 import dumps as qasm2_dumps

SUPPORTED_GATES = {
    'id': {'qubits': 1, 'params': 0, 'description': 'Identity gate'},
    'x': {'qubits': 1, 'params': 0, 'description': 'Pauli-X (NOT) gate'},
    'y': {'qubits': 1, 'params': 0, 'description': 'Pauli-Y gate'},
    'z': {'qubits': 1, 'params': 0, 'description': 'Pauli-Z (Phase-flip) gate'},
    'h': {'qubits': 1, 'params': 0, 'description': 'Hadamard gate'},
    's': {'qubits': 1, 'params': 0, 'description': 'S (Clifford Phase) gate'},
    'sdg': {'qubits': 1, 'params': 0, 'description': 'S dagger gate'},
    't': {'qubits': 1, 'params': 0, 'description': 'T (pi/8) gate'},
    'tdg': {'qubits': 1, 'params': 0, 'description': 'T dagger gate'},
    'rx': {'qubits': 1, 'params': 1, 'description': 'Rotation around X-axis'},
    'ry': {'qubits': 1, 'params': 1, 'description': 'Rotation around Y-axis'},
    'rz': {'qubits': 1, 'params': 1, 'description': 'Rotation around Z-axis'},
    'p': {'qubits': 1, 'params': 1, 'description': 'Phase rotation gate'},
    'cx': {'qubits': 2, 'params': 0, 'description': 'Controlled-NOT (CNOT) gate'},
    'cz': {'qubits': 2, 'params': 0, 'description': 'Controlled-Z gate'},
    'swap': {'qubits': 2, 'params': 0, 'description': 'SWAP gate'},
    'measure': {'qubits': 1, 'classical': 1, 'params': 0, 'description': 'Measurement into classical register'}
}

class CircuitValidationError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

def validate_circuit_definition(definition, max_qubits=16):
    """
    Validates JSON circuit schema.
    Structure:
    {
        "schema_version": "1.0",
        "num_qubits": 2,
        "num_classical_bits": 2,
        "operations": [
            {"gate": "h", "targets": [0]},
            {"gate": "cx", "targets": [0, 1]},
            {"gate": "measure", "targets": [0], "cbits": [0]},
            {"gate": "measure", "targets": [1], "cbits": [1]}
        ]
    }
    """
    if not isinstance(definition, dict):
        raise CircuitValidationError("Circuit definition must be a JSON object.")

    num_qubits = definition.get("num_qubits")
    if not isinstance(num_qubits, int) or num_qubits < 1 or num_qubits > max_qubits:
        raise CircuitValidationError(f"num_qubits must be an integer between 1 and {max_qubits}.")

    num_clbits = definition.get("num_classical_bits", num_qubits)
    if not isinstance(num_clbits, int) or num_clbits < 0 or num_clbits > max_qubits:
        raise CircuitValidationError(f"num_classical_bits must be an integer between 0 and {max_qubits}.")

    operations = definition.get("operations", [])
    if not isinstance(operations, list):
        raise CircuitValidationError("operations must be a list of gate instructions.")

    for idx, op in enumerate(operations):
        if not isinstance(op, dict):
            raise CircuitValidationError(f"Operation at index {idx} must be a dictionary.")

        gate_name = str(op.get("gate", "")).lower()
        if gate_name not in SUPPORTED_GATES:
            raise CircuitValidationError(
                f"Unsupported gate '{gate_name}' at operation {idx}.",
                details={"supported_gates": list(SUPPORTED_GATES.keys())}
            )

        gate_spec = SUPPORTED_GATES[gate_name]
        targets = op.get("targets", [])
        if not isinstance(targets, list) or len(targets) != gate_spec['qubits']:
            raise CircuitValidationError(
                f"Gate '{gate_name}' requires exactly {gate_spec['qubits']} target qubit(s) at operation {idx}."
            )

        for q in targets:
            if not isinstance(q, int) or q < 0 or q >= num_qubits:
                raise CircuitValidationError(
                    f"Target qubit index {q} is out of range [0, {num_qubits - 1}] at operation {idx}."
                )

        if len(targets) == 2 and targets[0] == targets[1]:
            raise CircuitValidationError(f"Two-qubit gate '{gate_name}' cannot have identical control and target qubits at operation {idx}.")

        params = op.get("params", [])
        expected_params = gate_spec.get('params', 0)
        if len(params) != expected_params:
            raise CircuitValidationError(
                f"Gate '{gate_name}' expects {expected_params} parameter(s), got {len(params)} at operation {idx}."
            )

        for p in params:
            if not isinstance(p, (int, float)) or math.isnan(p) or math.isinf(p):
                raise CircuitValidationError(f"Gate '{gate_name}' parameter must be a finite real number at operation {idx}.")

        if gate_name == 'measure':
            cbits = op.get("cbits", [])
            if not isinstance(cbits, list) or len(cbits) != 1:
                raise CircuitValidationError(f"Measurement at operation {idx} must specify exactly one target classical bit.")
            c = cbits[0]
            if not isinstance(c, int) or c < 0 or c >= num_clbits:
                raise CircuitValidationError(f"Classical bit index {c} out of range [0, {num_clbits - 1}] at operation {idx}.")

    return True

def build_qiskit_circuit(definition, max_qubits=16):
    """Constructs an executable Qiskit QuantumCircuit instance from validated JSON definition."""
    validate_circuit_definition(definition, max_qubits=max_qubits)

    num_qubits = definition["num_qubits"]
    num_clbits = definition.get("num_classical_bits", num_qubits)

    qc = QuantumCircuit(num_qubits, num_clbits)

    for op in definition.get("operations", []):
        gate_name = op["gate"].lower()
        targets = op["targets"]
        params = op.get("params", [])

        if gate_name == 'id':
            qc.id(targets[0])
        elif gate_name == 'x':
            qc.x(targets[0])
        elif gate_name == 'y':
            qc.y(targets[0])
        elif gate_name == 'z':
            qc.z(targets[0])
        elif gate_name == 'h':
            qc.h(targets[0])
        elif gate_name == 's':
            qc.s(targets[0])
        elif gate_name == 'sdg':
            qc.sdg(targets[0])
        elif gate_name == 't':
            qc.t(targets[0])
        elif gate_name == 'tdg':
            qc.tdg(targets[0])
        elif gate_name == 'rx':
            qc.rx(float(params[0]), targets[0])
        elif gate_name == 'ry':
            qc.ry(float(params[0]), targets[0])
        elif gate_name == 'rz':
            qc.rz(float(params[0]), targets[0])
        elif gate_name == 'p':
            qc.p(float(params[0]), targets[0])
        elif gate_name == 'cx':
            qc.cx(targets[0], targets[1])
        elif gate_name == 'cz':
            qc.cz(targets[0], targets[1])
        elif gate_name == 'swap':
            qc.swap(targets[0], targets[1])
        elif gate_name == 'measure':
            qc.measure(targets[0], op["cbits"][0])

    return qc

def export_to_qasm(qc):
    """Exports QuantumCircuit to OpenQASM 2.0 representation."""
    try:
        return qasm2_dumps(qc)
    except Exception as e:
        return f"// QASM export notice: {str(e)}"
