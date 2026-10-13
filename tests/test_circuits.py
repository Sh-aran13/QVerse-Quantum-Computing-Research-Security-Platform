import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.circuits.models import Circuit
from apps.experiments.models import Experiment, ExperimentResult
from quantum_engine.circuit_builder import (
    validate_circuit_definition, CircuitValidationError,
    build_qiskit_circuit, export_to_qasm
)
from quantum_engine.simulator import CircuitSimulator

class CircuitEngineAndApiTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="circuit_tester",
            password="StrongPassword123!"
        )
        self.client.login(username="circuit_tester", password="StrongPassword123!")

        # Standard Bell State definition
        self.bell_circuit_def = {
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

    def test_validation_success_and_failures(self):
        # Valid circuit passes
        self.assertTrue(validate_circuit_definition(self.bell_circuit_def))

        # Unsupported gate raises error
        invalid_gate = {
            "schema_version": "1.0",
            "num_qubits": 2,
            "operations": [{"gate": "magic_teleport", "targets": [0]}]
        }
        with self.assertRaises(CircuitValidationError):
            validate_circuit_definition(invalid_gate)

        # Out-of-range qubit index raises error
        out_of_range = {
            "schema_version": "1.0",
            "num_qubits": 2,
            "operations": [{"gate": "x", "targets": [5]}]
        }
        with self.assertRaises(CircuitValidationError):
            validate_circuit_definition(out_of_range)

    def test_qiskit_circuit_building_and_aer_simulation(self):
        qc = build_qiskit_circuit(self.bell_circuit_def)
        self.assertEqual(qc.num_qubits, 2)
        self.assertEqual(qc.num_clbits, 2)
        qasm_str = export_to_qasm(qc)
        self.assertIn('OPENQASM', qasm_str)

        simulator = CircuitSimulator()
        sim_res = simulator.simulate(self.bell_circuit_def, shots=1000, seed=42)
        counts = sim_res["counts"]

        # In Bell state (|00> + |11>)/sqrt(2), counts should be dominantly '00' and '11'
        self.assertIn('00', counts)
        self.assertIn('11', counts)
        # Check that total shots is 1000
        self.assertEqual(sum(counts.values()), 1000)
        # Check execution metrics
        self.assertGreater(sim_res["metrics"]["execution_time_ms"], 0)
        self.assertEqual(sim_res["metrics"]["qubit_count"], 2)

    def test_x_gate_computational_basis_flip(self):
        x_flip_def = {
            "schema_version": "1.0",
            "num_qubits": 1,
            "num_classical_bits": 1,
            "operations": [
                {"gate": "x", "targets": [0]},
                {"gate": "measure", "targets": [0], "cbits": [0]}
            ]
        }
        simulator = CircuitSimulator()
        res = simulator.simulate(x_flip_def, shots=500, seed=123)
        # State flips deterministically from |0> to |1>
        self.assertEqual(res["counts"].get('1'), 500)

    def test_circuit_crud_and_simulation_api(self):
        # Create circuit via API
        create_res = self.client.post(
            '/api/v1/circuits/',
            data=json.dumps({
                "name": "API Bell State",
                "num_qubits": 2,
                "circuit_definition": self.bell_circuit_def
            }),
            content_type='application/json'
        )
        self.assertEqual(create_res.status_code, 201)
        circuit_id = create_res.json()['id']

        # Validate endpoint
        val_res = self.client.post(f'/api/v1/circuits/{circuit_id}/validate/')
        self.assertEqual(val_res.status_code, 200)
        self.assertTrue(val_res.json()['valid'])

        # Simulate endpoint
        sim_api_res = self.client.post(
            f'/api/v1/circuits/{circuit_id}/simulate/',
            data=json.dumps({"shots": 1000, "seed": 42}),
            content_type='application/json'
        )
        self.assertEqual(sim_api_res.status_code, 200)
        sim_data = sim_api_res.json()
        self.assertIn('counts', sim_data)
        self.assertIn('probabilities', sim_data)
        self.assertIsNotNone(sim_data.get('experiment_id'))

        # Verify persisted experiment record
        exp = Experiment.objects.get(id=sim_data['experiment_id'])
        self.assertEqual(exp.status, "SUCCEEDED")
        self.assertIsNotNone(exp.result)
        self.assertEqual(exp.result.shots, 1000)

        # Export endpoint
        export_res = self.client.get(f'/api/v1/circuits/{circuit_id}/export/')
        self.assertEqual(export_res.status_code, 200)
        self.assertIn('qasm', export_res.json())
