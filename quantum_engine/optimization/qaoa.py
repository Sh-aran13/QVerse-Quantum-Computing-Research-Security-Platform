"""
Quantum Approximate Optimization Algorithm (QAOA) for Max-Cut
Implements genuine parameterized QAOA circuit, classical optimization loop (COBYLA/Nelder-Mead),
and classical brute-force exact solver baseline for bounded graphs.
"""

import time
import networkx as nx
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

def calculate_maxcut_value(bitstring: str, graph: nx.Graph) -> int:
    """Calculates the Max-Cut value for a given binary bitstring partition."""
    # Qiskit bitstring order is little-endian (rightmost bit is node 0)
    rev = bitstring[::-1]
    cut = 0
    for u, v in graph.edges():
        if u < len(rev) and v < len(rev):
            if rev[u] != rev[v]:
                cut += 1
    return cut

def classical_exact_maxcut(graph: nx.Graph):
    """Classical exhaustive search finding the true maximum cut for bounded graphs."""
    start_time = time.perf_counter()
    n = graph.number_of_nodes()
    best_cut = -1
    best_partition = ""

    for i in range(2 ** n):
        # Format bitstring
        bitstring = format(i, f'0{n}b')
        cut = calculate_maxcut_value(bitstring, graph)
        if cut > best_cut:
            best_cut = cut
            best_partition = bitstring

    duration_ms = round((time.perf_counter() - start_time) * 1000, 4)
    return {
        "best_cut": best_cut,
        "best_partition": best_partition,
        "total_evaluations": 2 ** n,
        "execution_time_ms": duration_ms
    }

def build_qaoa_circuit(graph: nx.Graph, gamma: list, beta: list):
    """
    Constructs an authentic QAOA circuit for Max-Cut:
    - Layer of Hadamards
    - p alternating layers of Problem Unitary U(C, gamma) and Mixer Unitary U(B, beta)
    """
    n = graph.number_of_nodes()
    p = len(gamma)
    qc = QuantumCircuit(n, n)

    # Initial equal superposition
    qc.h(range(n))

    for layer in range(p):
        g = gamma[layer]
        b = beta[layer]

        # Problem Unitary: exp(-i * gamma * C) -> For each edge (u, v): CX - RZ(2*gamma) - CX
        for u, v in graph.edges():
            qc.cx(u, v)
            qc.rz(2 * g, v)
            qc.cx(u, v)

        # Mixer Unitary: exp(-i * beta * B) -> RX(2*beta) on each qubit
        for q in range(n):
            qc.rx(2 * b, q)

    qc.measure(range(n), range(n))
    return qc

def run_qaoa_maxcut(
    edges: list = None,
    num_nodes: int = 4,
    p_layers: int = 1,
    max_evals: int = 15,
    shots: int = 1024,
    seed: int = 42
):
    """
    Executes QAOA on Qiskit Aer to solve the Max-Cut problem.
    Runs classical optimizer loop to find optimal variational parameters (gamma, beta).
    """
    start_total_time = time.perf_counter()

    # Build NetworkX Graph
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    if edges:
        for e in edges:
            G.add_edge(e[0], e[1])
    else:
        # Default Ring graph
        for i in range(num_nodes):
            G.add_edge(i, (i + 1) % num_nodes)

    # 1. Classical exact baseline
    classical_sol = classical_exact_maxcut(G)

    backend = AerSimulator()
    convergence_history = []
    eval_count = 0

    def objective_fn(params):
        nonlocal eval_count
        eval_count += 1
        gamma = params[:p_layers]
        beta = params[p_layers:]

        qc = build_qaoa_circuit(G, gamma, beta)
        compiled_qc = transpile(qc, backend)
        job = backend.run(compiled_qc, shots=shots, seed_simulator=seed)
        counts = job.result().get_counts()
        if isinstance(counts, list):
            counts = counts[0]

        # Calculate expectation value of Max-Cut (negative for minimization)
        expected_cut = 0.0
        for bitstr, count in counts.items():
            cut = calculate_maxcut_value(bitstr, G)
            expected_cut += (cut * count) / shots

        neg_obj = -expected_cut
        convergence_history.append({
            "evaluation": eval_count,
            "cost_value": round(expected_cut, 3)
        })
        return neg_obj

    # Initial parameter guess
    init_params = [0.5] * p_layers + [0.5] * p_layers

    opt_res = minimize(
        objective_fn,
        init_params,
        method='COBYLA',
        options={'maxiter': max_evals}
    )

    opt_gamma = opt_res.x[:p_layers]
    opt_beta = opt_res.x[p_layers:]

    # Final execution with optimal parameters
    final_qc = build_qaoa_circuit(G, opt_gamma, opt_beta)
    compiled_final = transpile(final_qc, backend)
    final_job = backend.run(compiled_final, shots=shots, seed_simulator=seed)
    final_counts = final_job.result().get_counts()
    if isinstance(final_counts, list):
        final_counts = final_counts[0]

    # Best measured partition
    best_measured_partition = max(final_counts, key=final_counts.get)
    best_measured_cut = calculate_maxcut_value(best_measured_partition, G)

    total_time_ms = round((time.perf_counter() - start_total_time) * 1000, 2)
    approximation_ratio = round(best_measured_cut / max(1, classical_sol["best_cut"]), 3)

    return {
        "graph": {
            "num_nodes": num_nodes,
            "edges": list(G.edges()),
            "num_edges": G.number_of_edges()
        },
        "qaoa_result": {
            "p_layers": p_layers,
            "best_measured_partition": best_measured_partition,
            "best_measured_cut": best_measured_cut,
            "approximation_ratio": approximation_ratio,
            "optimal_gamma": [round(float(x), 4) for x in opt_gamma],
            "optimal_beta": [round(float(x), 4) for x in opt_beta],
            "circuit_depth": final_qc.depth(),
            "gate_count": sum(final_qc.count_ops().values()) - final_qc.count_ops().get('measure', 0),
            "evaluations_run": eval_count,
            "counts": final_counts,
            "convergence_history": convergence_history[:15]
        },
        "classical_baseline": classical_sol,
        "execution_time_ms": total_time_ms,
        "qasm": export_to_qasm(final_qc)
    }
