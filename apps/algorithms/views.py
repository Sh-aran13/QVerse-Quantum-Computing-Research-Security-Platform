from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule, ExperimentResult
from apps.audit.models import AuditEvent
from quantum_engine.algorithms.grover import run_grover_search
from quantum_engine.algorithms.teleportation import run_teleportation
from quantum_engine.algorithms.qft import run_qft
from quantum_engine.algorithms.entanglement import run_entanglement_experiment, SUPPORTED_STATES

ALGORITHM_REGISTRY = {
    'grover': {
        'name': "Grover's Search Algorithm",
        'description': "Quantum search providing quadratic speedup over classical brute-force.",
        'complexity': "O(sqrt(N)) vs Classical O(N)",
        'qubit_range': [2, 5]
    },
    'teleportation': {
        'name': "Quantum Teleportation",
        'description': "Disembodied transfer of an unknown quantum state using Bell entanglement and 2 classical bits.",
        'complexity': "Exact state transfer with unit theoretical fidelity",
        'qubit_range': [3, 3]
    },
    'qft': {
        'name': "Quantum Fourier Transform",
        'description': "Quantum analogue of the discrete Fourier transform mapping computational states to frequency phase states.",
        'complexity': "O(n^2) vs Classical FFT O(n 2^n)",
        'qubit_range': [1, 6]
    },
    'entanglement': {
        'name': "Quantum Entanglement & Non-locality",
        'description': "Preparation and measurement correlation analysis of the 4 canonical Bell states and 3-qubit GHZ state.",
        'complexity': "Non-classical Bell correlation",
        'qubit_range': [2, 3]
    }
}

class AlgorithmListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response([
            {"id": key, **meta} for key, meta in ALGORITHM_REGISTRY.items()
        ])

class AlgorithmMetadataView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, algorithm):
        alg = algorithm.lower()
        if alg not in ALGORITHM_REGISTRY:
            return Response({"error": f"Algorithm '{algorithm}' not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ALGORITHM_REGISTRY[alg])

class AlgorithmRunView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, algorithm):
        user = get_or_create_open_researcher(request)
        alg = algorithm.lower()
        if alg not in ALGORITHM_REGISTRY:
            return Response({"error": f"Algorithm '{algorithm}' is not a registered algorithm."}, status=status.HTTP_400_BAD_REQUEST)

        params = request.data or {}
        shots = int(params.get('shots', 1024))
        seed = params.get('seed')
        save_as_exp = params.get('save_as_experiment', True)

        try:
            if alg == 'grover':
                marked_state = str(params.get('marked_state', '101'))
                iterations = params.get('iterations')
                res = run_grover_search(marked_state, shots=shots, iterations=iterations, seed=seed)
                exp_type = 'grover_search'
                exp_desc = f"Grover search for marked state |{marked_state}⟩"
            elif alg == 'teleportation':
                theta = float(params.get('theta', 1.047))
                phi = float(params.get('phi', 0.523))
                res = run_teleportation(theta=theta, phi=phi, shots=shots, seed=seed)
                exp_type = 'quantum_teleportation'
                exp_desc = f"Teleportation of state θ={round(theta,2)}, φ={round(phi,2)}"
            elif alg == 'qft':
                num_qubits = int(params.get('num_qubits', 3))
                inverse = bool(params.get('inverse', False))
                input_state = int(params.get('input_state', 1))
                res = run_qft(num_qubits=num_qubits, inverse=inverse, input_state=input_state, shots=shots, seed=seed)
                exp_type = 'inverse_qft' if inverse else 'quantum_fourier_transform'
                exp_desc = f"{'Inverse ' if inverse else ''}QFT on {num_qubits} qubits (input |{input_state}⟩)"
            elif alg == 'entanglement':
                state_type = str(params.get('state_type', 'phi_plus'))
                res = run_entanglement_experiment(state_type=state_type, shots=shots, seed=seed)
                exp_type = f"entanglement_{state_type}"
                exp_desc = f"Entanglement correlation experiment: {SUPPORTED_STATES[state_type]['desc']}"
        except Exception as e:
            return Response({"error": f"Execution error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        experiment_id = None
        if save_as_exp:
            exp = Experiment.objects.create(
                owner=user,
                name=params.get('experiment_name') or f"Alg: {ALGORITHM_REGISTRY[alg]['name']}",
                module=ExperimentModule.ALGORITHMS,
                experiment_type=exp_type,
                description=exp_desc,
                configuration=params,
                methodology_notes=f"Executed on Qiskit Aer with finite-shot quantum measurement. Complexity: {ALGORITHM_REGISTRY[alg]['complexity']}",
                status=ExperimentStatus.SUCCEEDED,
                started_at=timezone.now(),
                completed_at=timezone.now()
            )
            ExperimentResult.objects.create(
                experiment=exp,
                result_data={
                    "counts": res["counts"],
                    "probabilities": res["probabilities"]
                },
                metrics=res["metrics"],
                backend_name=res["metrics"]["backend_name"],
                shots=shots,
                seed=seed,
                execution_time_ms=res["metrics"]["execution_time_ms"],
                circuit_depth=res["metrics"]["circuit_depth"],
                gate_count=res["metrics"]["gate_count"],
                qubit_count=res["metrics"]["qubit_count"]
            )
            experiment_id = str(exp.id)

        res["experiment_id"] = experiment_id
        return Response(res)
