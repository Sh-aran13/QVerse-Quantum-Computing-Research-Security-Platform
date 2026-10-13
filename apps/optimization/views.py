from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.optimization.models import OptimizationRun
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from quantum_engine.optimization.qaoa import run_qaoa_maxcut

class QAOARunView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_or_create_open_researcher(request)
        num_nodes = int(request.data.get('num_nodes', 4))
        p_layers = int(request.data.get('p_layers', 1))
        max_evals = int(request.data.get('max_evals', 12))
        shots = int(request.data.get('shots', 1024))
        seed = int(request.data.get('seed', 42))
        edges = request.data.get('edges')

        try:
            res = run_qaoa_maxcut(
                edges=edges,
                num_nodes=num_nodes,
                p_layers=p_layers,
                max_evals=max_evals,
                shots=shots,
                seed=seed
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Persist as Experiment
        exp = Experiment.objects.create(
            owner=user,
            name=f"QAOA Max-Cut (N={num_nodes}, p={p_layers})",
            module=ExperimentModule.OPTIMIZATION,
            experiment_type="qaoa_maxcut",
            description=f"Variational QAOA Max-Cut optimization on graph with {num_nodes} nodes and {res['graph']['num_edges']} edges.",
            configuration=request.data,
            methodology_notes=f"COBYLA classical optimizer loop over {res['qaoa_result']['evaluations_run']} evaluations. Exact baseline computed via classical exhaustive search.",
            status=ExperimentStatus.SUCCEEDED,
            started_at=timezone.now(),
            completed_at=timezone.now()
        )

        # Persist OptimizationRun
        OptimizationRun.objects.create(
            experiment=exp,
            problem_definition=res["graph"],
            algorithm_configuration={"p_layers": p_layers, "shots": shots, "seed": seed},
            best_solution=res["qaoa_result"]["best_measured_partition"],
            objective_value=res["qaoa_result"]["best_measured_cut"],
            convergence_history=res["qaoa_result"]["convergence_history"]
        )

        res["experiment_id"] = str(exp.id)
        return Response(res)
