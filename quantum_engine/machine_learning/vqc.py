"""
Hybrid Quantum Machine Learning (QML) Engine
Implements a Parameterized Quantum Classifier (VQC) using Angle Embedding & Variational Rotations,
evaluated against a Classical Scikit-Learn Logistic Regression Baseline.
"""

import time
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from quantum_engine.circuit_builder import export_to_qasm

def generate_educational_dataset(n_samples: int = 40, seed: int = 42):
    """Generates synthetic 2D linearly separable quantum classification benchmark data."""
    rng = np.random.RandomState(seed)
    # 2 features scaled between 0 and pi for angle encoding
    X0 = rng.uniform(0.2, 1.4, size=(n_samples // 2, 2))
    y0 = np.zeros(n_samples // 2, dtype=int)

    X1 = rng.uniform(1.8, 3.0, size=(n_samples // 2, 2))
    y1 = np.ones(n_samples // 2, dtype=int)

    X = np.vstack([X0, X1])
    y = np.concatenate([y0, y1])

    # Shuffle
    indices = rng.permutation(n_samples)
    return X[indices], y[indices]

def build_vqc_circuit(features: np.ndarray, weights: np.ndarray):
    """
    Constructs a 2-qubit Variational Quantum Classifier circuit:
    - Feature Encoding: Angle embedding via RY rotations
    - Variational Ansatz: Parameterized RZ and RY rotations + Entangling CNOT
    """
    qc = QuantumCircuit(2, 1)

    # 1. Feature Map (Angle Encoding)
    qc.ry(float(features[0]), 0)
    qc.ry(float(features[1]), 1)

    # 2. Entanglement Layer
    qc.cx(0, 1)

    # 3. Parameterized Ansatz Layer
    qc.rz(float(weights[0]), 0)
    qc.ry(float(weights[1]), 0)
    qc.rz(float(weights[2]), 1)
    qc.ry(float(weights[3]), 1)

    # Measure parity / target qubit into classical bit
    qc.measure(1, 0)
    return qc

def run_hybrid_quantum_ml(
    n_samples: int = 40,
    max_epochs: int = 10,
    shots: int = 512,
    seed: int = 42
):
    """
    Executes real hybrid quantum optimization loop:
    Evaluates quantum circuit expectations against Scikit-Learn classical baseline.
    """
    start_total_time = time.perf_counter()
    X, y = generate_educational_dataset(n_samples=n_samples, seed=seed)

    # Split 75% train, 25% test
    split = int(0.75 * n_samples)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    backend = AerSimulator()

    # --- 1. Classical ML Baseline (Logistic Regression) ---
    c_start = time.perf_counter()
    clf = LogisticRegression()
    clf.fit(X_train, y_train)
    c_preds = clf.predict(X_test)
    c_time_ms = round((time.perf_counter() - c_start) * 1000, 2)

    classical_metrics = {
        "accuracy": round(accuracy_score(y_test, c_preds), 4),
        "precision": round(precision_score(y_test, c_preds, zero_division=0), 4),
        "recall": round(recall_score(y_test, c_preds, zero_division=0), 4),
        "f1": round(f1_score(y_test, c_preds, zero_division=0), 4),
        "training_time_ms": c_time_ms
    }

    # --- 2. Variational Quantum Classifier (VQC) Hybrid Loop ---
    q_start = time.perf_counter()
    loss_history = []
    current_epoch = 0

    def predict_quantum(features, weights):
        qc = build_vqc_circuit(features, weights)
        compiled_qc = transpile(qc, backend)
        job = backend.run(compiled_qc, shots=shots, seed_simulator=seed)
        counts = job.result().get_counts()
        if isinstance(counts, list):
            counts = counts[0]
        # P(1)
        prob_1 = counts.get('1', 0) / shots
        return prob_1

    def cost_function(weights):
        nonlocal current_epoch
        loss = 0.0
        # Compute MSE across train set
        for feat, target in zip(X_train, y_train):
            p1 = predict_quantum(feat, weights)
            loss += (p1 - target) ** 2
        loss /= len(X_train)
        current_epoch += 1
        loss_history.append({"epoch": current_epoch, "loss": round(float(loss), 4)})
        return loss

    # Initialize variational weights
    init_weights = np.array([0.1, 0.2, 0.3, 0.4])

    opt = minimize(
        cost_function,
        init_weights,
        method='COBYLA',
        options={'maxiter': max_epochs}
    )

    opt_weights = opt.x

    # Test evaluation
    q_preds = []
    for feat in X_test:
        p1 = predict_quantum(feat, opt_weights)
        q_preds.append(1 if p1 >= 0.5 else 0)

    q_time_ms = round((time.perf_counter() - q_start) * 1000, 2)

    quantum_metrics = {
        "accuracy": round(accuracy_score(y_test, q_preds), 4),
        "precision": round(precision_score(y_test, q_preds, zero_division=0), 4),
        "recall": round(recall_score(y_test, q_preds, zero_division=0), 4),
        "f1": round(f1_score(y_test, q_preds, zero_division=0), 4),
        "trainable_parameters": 4,
        "circuit_qubits": 2,
        "training_time_ms": q_time_ms,
        "loss_history": loss_history[:max_epochs]
    }

    sample_qc = build_vqc_circuit(X_train[0], opt_weights)

    return {
        "dataset": {
            "total_samples": n_samples,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_features": 2
        },
        "quantum_classifier": quantum_metrics,
        "classical_baseline": classical_metrics,
        "execution_time_ms": round((time.perf_counter() - start_total_time) * 1000, 2),
        "qasm": export_to_qasm(sample_qc)
    }
