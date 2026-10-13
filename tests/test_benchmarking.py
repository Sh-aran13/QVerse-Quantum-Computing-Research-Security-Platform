import json
from django.test import TestCase, Client
from apps.experiments.models import Experiment
from apps.benchmarking.models import BenchmarkRun
from quantum_engine.benchmarking.search_benchmark import run_search_benchmark, run_classical_linear_search
from quantum_engine.transpilation import analyze_circuit_structure, optimize_quantum_circuit

class Phase4BenchmarkingAndOptimizerTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Circuit containing self-inverse redundant gates: H*H = I, CX*CX = I
        self.redundant_circuit = {
            "schema_version": "1.0",
            "num_qubits": 2,
            "num_classical_bits": 2,
            "operations": [
                {"gate": "h", "targets": [0]},
                {"gate": "h", "targets": [0]},
                {"gate": "cx", "targets": [0, 1]},
                {"gate": "cx", "targets": [0, 1]},
                {"gate": "x", "targets": [0]},
                {"gate": "measure", "targets": [0], "cbits": [0]}
            ]
        }

    def test_classical_linear_search_baseline(self):
        res = run_classical_linear_search(search_space_size=16, target_index=7)
        self.assertEqual(res["found_index"], 7)
        self.assertEqual(res["evaluations"], 8)
        self.assertEqual(res["complexity"], "O(N)")

    def test_quantum_vs_classical_search_benchmark(self):
        bench = run_search_benchmark(marked_state='10', shots=500, seed=42)
        self.assertEqual(bench["search_space_size"], 4)
        self.assertIn("quantum", bench)
        self.assertIn("classical", bench)
        self.assertEqual(bench["quantum"]["evaluations_or_iterations"], 1)
        self.assertGreaterEqual(bench["classical"]["evaluations"], 1)

    def test_circuit_analysis(self):
        analysis = analyze_circuit_structure(self.redundant_circuit)
        self.assertEqual(analysis["num_qubits"], 2)
        self.assertEqual(analysis["total_gates"], 5)
        self.assertEqual(analysis["num_measurements"], 1)

    def test_circuit_optimization_pass_cancellation(self):
        # Optimization Level 2 should eliminate the redundant H-H and CX-CX gate pairs
        opt_res = optimize_quantum_circuit(self.redundant_circuit, optimization_level=2)
        # Original has 5 unitaries (H, H, CX, CX, X)
        self.assertEqual(opt_res["original_metrics"]["gate_count"], 5)
        # Transpiled circuit with cancellations must have fewer gates
        self.assertLess(opt_res["optimized_metrics"]["gate_count"], 5)
        self.assertGreater(opt_res["comparison"]["depth_reduction"], 0)

    def test_benchmarking_api_open_access(self):
        # Benchmark run should work openly without requiring login
        res = self.client.post(
            '/api/v1/benchmarks/run/',
            data=json.dumps({"marked_state": "10", "shots": 500, "seed": 42}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('experiment_id', data)
        self.assertTrue(Experiment.objects.filter(id=data['experiment_id']).exists())
        self.assertEqual(BenchmarkRun.objects.filter(experiment_id=data['experiment_id']).count(), 2)

    def test_circuit_optimizer_api_open_access(self):
        res = self.client.post(
            '/api/v1/circuit-optimizer/optimize/',
            data=json.dumps({
                "circuit_definition": self.redundant_circuit,
                "optimization_level": 2
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('optimized_metrics', data)
        self.assertIn('comparison', data)
