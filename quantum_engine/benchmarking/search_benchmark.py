"""
Benchmarking Engine: Quantum vs Classical Computations
Provides scientific, reproducible comparisons between quantum methods and classical baselines.
"""

import time
import math
import random
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from apps.benchmarking.models import BenchmarkRun
from quantum_engine.algorithms.grover import run_grover_search

def run_classical_linear_search(search_space_size: int, target_index: int):
    """Classical $O(N)$ linear search baseline."""
    start_time = time.perf_counter()
    evaluations = 0
    found_index = -1
    for i in range(search_space_size):
        evaluations += 1
        if i == target_index:
            found_index = i
            break
    duration_ms = (time.perf_counter() - start_time) * 1000
    return {
        "found_index": found_index,
        "evaluations": evaluations,
        "execution_time_ms": round(duration_ms, 4),
        "complexity": "O(N)"
    }

def run_search_benchmark(marked_state: str = '101', shots: int = 1024, seed: int = 42):
    """
    Executes head-to-head comparison:
    Grover Search (Quantum Aer) vs Classical Linear Search
    """
    n = len(marked_state)
    N = 2 ** n
    target_idx = int(marked_state, 2)

    # 1. Classical Execution
    classical_res = run_classical_linear_search(N, target_idx)

    # 2. Quantum Execution
    quantum_res = run_grover_search(marked_state, shots=shots, seed=seed)

    # Analytical comparison
    speedup_ratio = round(classical_res["evaluations"] / max(1, quantum_res["iterations"]), 2)

    return {
        "problem_type": "Unstructured Database Search",
        "search_space_size": N,
        "marked_state": marked_state,
        "quantum": {
            "method": "Grover's Amplitude Amplification",
            "evaluations_or_iterations": quantum_res["iterations"],
            "complexity": "O(√N)",
            "execution_time_ms": quantum_res["metrics"]["execution_time_ms"],
            "success_probability": quantum_res["measured_success_probability"],
            "circuit_depth": quantum_res["metrics"]["circuit_depth"],
            "gate_count": quantum_res["metrics"]["gate_count"],
            "shots": shots,
            "counts": quantum_res["counts"]
        },
        "classical": {
            "method": "Classical Brute-Force Linear Search",
            "evaluations": classical_res["evaluations"],
            "complexity": "O(N)",
            "execution_time_ms": classical_res["execution_time_ms"],
            "success_probability": 1.0
        },
        "scientific_notes": {
            "theoretical_quantum_speedup": f"√{N} ≈ {round(math.sqrt(N), 1)} queries vs {N} classical queries",
            "query_reduction_factor": speedup_ratio,
            "simulation_overhead_disclosure": "Quantum execution wall-clock time reflects classical statevector/density matrix simulation on CPU and does not equate to physical quantum processor execution speed."
        }
    }
