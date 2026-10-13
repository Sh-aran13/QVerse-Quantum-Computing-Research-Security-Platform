from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.quantum_ml.models import QuantumMLRun
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from quantum_engine.machine_learning.vqc import run_hybrid_quantum_ml

class QuantumMLExperimentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_or_create_open_researcher(request)
        n_samples = int(request.data.get('n_samples', 30))
        max_epochs = int(request.data.get('max_epochs', 8))
        shots = int(request.data.get('shots', 512))
        seed = int(request.data.get('seed', 42))

        try:
            res = run_hybrid_quantum_ml(
                n_samples=n_samples,
                max_epochs=max_epochs,
                shots=shots,
                seed=seed
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Persist as Experiment
        exp = Experiment.objects.create(
            owner=user,
            name=f"VQC vs Classical ML (N={n_samples})",
            module=ExperimentModule.QUANTUM_ML,
            experiment_type="hybrid_quantum_classifier",
            description=f"Variational quantum classification benchmark against Scikit-Learn Logistic Regression on 2D synthetic dataset.",
            configuration=request.data,
            methodology_notes=f"Hybrid COBYLA optimization loop with angle embedding. Quantum Accuracy: {res['quantum_classifier']['accuracy']}, Classical: {res['classical_baseline']['accuracy']}",
            status=ExperimentStatus.SUCCEEDED,
            started_at=timezone.now(),
            completed_at=timezone.now()
        )

        # Persist QuantumMLRun
        QuantumMLRun.objects.create(
            experiment=exp,
            dataset_metadata=res["dataset"],
            model_configuration={"ansatz": "2-qubit VQC", "trainable_params": 4, "shots": shots},
            training_metrics=res["quantum_classifier"],
            evaluation_metrics=res["classical_baseline"],
            random_seed=seed
        )

        res["experiment_id"] = str(exp.id)
        return Response(res)
