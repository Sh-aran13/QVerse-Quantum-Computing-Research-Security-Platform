import json
from django.test import TestCase, Client
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from apps.optimization.models import OptimizationRun
from apps.quantum_ml.models import QuantumMLRun
from quantum_engine.optimization.qaoa import run_qaoa_maxcut, classical_exact_maxcut
from quantum_engine.machine_learning.vqc import run_hybrid_quantum_ml

class Phases6And7AdvancedResearchTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_classical_exact_maxcut_baseline(self):
        import networkx as nx
        G = nx.cycle_graph(4) # 4-cycle graph has exact Max-Cut = 4 (alternating 0101)
        sol = classical_exact_maxcut(G)
        self.assertEqual(sol["best_cut"], 4)
        self.assertEqual(sol["total_evaluations"], 16)

    def test_qaoa_maxcut_execution_and_approximation(self):
        # 4-node ring graph
        res = run_qaoa_maxcut(num_nodes=4, p_layers=1, max_evals=6, shots=500, seed=42)
        self.assertIn("qaoa_result", res)
        self.assertIn("classical_baseline", res)
        self.assertEqual(res["graph"]["num_nodes"], 4)
        self.assertGreater(res["qaoa_result"]["best_measured_cut"], 0)
        self.assertGreater(res["qaoa_result"]["approximation_ratio"], 0.5)

    def test_qaoa_api_and_persistence(self):
        res = self.client.post(
            '/api/v1/optimization/qaoa/run/',
            data=json.dumps({"num_nodes": 4, "p_layers": 1, "max_evals": 5}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('experiment_id', data)
        exp = Experiment.objects.get(id=data['experiment_id'])
        self.assertEqual(exp.module, ExperimentModule.OPTIMIZATION)
        self.assertTrue(hasattr(exp, 'optimization_run'))

    def test_hybrid_quantum_ml_execution_and_metrics(self):
        res = run_hybrid_quantum_ml(n_samples=20, max_epochs=4, shots=200, seed=42)
        self.assertIn("quantum_classifier", res)
        self.assertIn("classical_baseline", res)
        self.assertGreaterEqual(res["quantum_classifier"]["accuracy"], 0.0)
        self.assertGreaterEqual(res["classical_baseline"]["accuracy"], 0.0)
        self.assertEqual(res["quantum_classifier"]["trainable_parameters"], 4)

    def test_quantum_ml_api_and_persistence(self):
        res = self.client.post(
            '/api/v1/quantum-ml/run/',
            data=json.dumps({"n_samples": 20, "max_epochs": 4}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('experiment_id', data)
        exp = Experiment.objects.get(id=data['experiment_id'])
        self.assertEqual(exp.module, ExperimentModule.QUANTUM_ML)
        self.assertTrue(hasattr(exp, 'qml_run'))

    def test_experiment_manager_and_exports(self):
        from apps.accounts.open_access import get_or_create_open_researcher
        user = get_or_create_open_researcher()
        # Create sample experiment
        exp = Experiment.objects.create(
            owner=user,
            name="Sample Provenance Run",
            module=ExperimentModule.CIRCUIT_STUDIO,
            experiment_type="test_run",
            status=ExperimentStatus.SUCCEEDED
        )

        # JSON Export
        json_res = self.client.get(f'/api/v1/experiments/{exp.id}/export/json/')
        self.assertEqual(json_res.status_code, 200)
        self.assertEqual(json_res['Content-Type'], 'application/json')

        # CSV Export
        csv_res = self.client.get(f'/api/v1/experiments/{exp.id}/export/csv/')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res['Content-Type'], 'text/csv')

        # HTML Report Export
        report_res = self.client.get(f'/api/v1/experiments/{exp.id}/export/report/')
        self.assertEqual(report_res.status_code, 200)
        self.assertEqual(report_res['Content-Type'], 'text/html')
