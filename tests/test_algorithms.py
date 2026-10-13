import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.experiments.models import Experiment, ExperimentResult
from quantum_engine.algorithms.grover import run_grover_search
from quantum_engine.algorithms.teleportation import run_teleportation
from quantum_engine.algorithms.qft import run_qft
from quantum_engine.algorithms.entanglement import run_entanglement_experiment

class QuantumAlgorithmsLabTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="algorithm_tester",
            password="StrongPassword123!"
        )
        self.client.login(username="algorithm_tester", password="StrongPassword123!")

    def test_grover_search_correctness(self):
        # 3-qubit marked state '101'
        res = run_grover_search(marked_state='101', shots=1000, seed=42)
        self.assertEqual(res['marked_state'], '101')
        self.assertEqual(res['search_space_size'], 8)
        self.assertEqual(res['optimal_iterations'], 2)
        # Marked state '101' probability should be amplified significantly (> 85%)
        self.assertGreater(res['measured_success_probability'], 0.85)

    def test_teleportation_protocol_fidelity(self):
        # Arbitrary test state
        res = run_teleportation(theta=1.2, phi=0.8, shots=1000, seed=42)
        # Measured fidelity after feed-forward correction must equal 1.0 on ideal simulator
        self.assertEqual(res['measured_fidelity'], 1.0)
        self.assertEqual(res['metrics']['qubit_count'], 3)

    def test_qft_and_inverse_qft_execution(self):
        # QFT execution on 3 qubits
        res_qft = run_qft(num_qubits=3, inverse=False, input_state=1, shots=1000, seed=42)
        self.assertEqual(res_qft['num_qubits'], 3)
        self.assertEqual(sum(res_qft['counts'].values()), 1000)

        # Inverse QFT execution
        res_iqft = run_qft(num_qubits=3, inverse=True, input_state=0, shots=1000, seed=42)
        self.assertTrue(res_iqft['is_inverse'])

    def test_entanglement_bell_and_ghz_states(self):
        # Bell Phi+ state (|00> + |11>)
        res_phi = run_entanglement_experiment(state_type='phi_plus', shots=1000, seed=42)
        self.assertIn('00', res_phi['counts'])
        self.assertIn('11', res_phi['counts'])
        # Neither 01 nor 10 should appear in ideal Bell Phi+ state
        self.assertNotIn('01', res_phi['counts'])
        self.assertNotIn('10', res_phi['counts'])

        # GHZ 3-qubit state (|000> + |111>)
        res_ghz = run_entanglement_experiment(state_type='ghz', shots=1000, seed=42)
        self.assertIn('000', res_ghz['counts'])
        self.assertIn('111', res_ghz['counts'])
        self.assertEqual(res_ghz['metrics']['qubit_count'], 3)

    def test_algorithm_api_endpoints_and_experiment_persistence(self):
        # List algorithms
        list_res = self.client.get('/api/v1/algorithms/')
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 4)

        # Run Grover via API
        run_res = self.client.post(
            '/api/v1/algorithms/grover/run/',
            data=json.dumps({"marked_state": "10", "shots": 500, "seed": 42}),
            content_type='application/json'
        )
        self.assertEqual(run_res.status_code, 200)
        data = run_res.json()
        self.assertIn('experiment_id', data)
        self.assertIsNotNone(data['experiment_id'])

        # Verify database record
        exp = Experiment.objects.get(id=data['experiment_id'])
        self.assertEqual(exp.status, "SUCCEEDED")
        self.assertEqual(exp.experiment_type, "grover_search")
        self.assertIsNotNone(exp.result)
