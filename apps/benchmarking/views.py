from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from apps.benchmarking.models import BenchmarkRun
from quantum_engine.benchmarking.search_benchmark import run_search_benchmark

class BenchmarkRunView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_or_create_open_researcher(request)
        benchmark_type = request.data.get('benchmark_type', 'grover_vs_classical')
        marked_state = request.data.get('marked_state', '101')
        shots = int(request.data.get('shots', 1024))
        seed = int(request.data.get('seed', 42))

        if benchmark_type == 'grover_vs_classical':
            result = run_search_benchmark(marked_state=marked_state, shots=shots, seed=seed)
        else:
            return Response({"error": f"Unsupported benchmark type '{benchmark_type}'"}, status=status.HTTP_400_BAD_REQUEST)

        # Persist as reproducible Experiment
        exp = Experiment.objects.create(
            owner=user,
            name=f"Benchmark: Grover vs Classical (N={result['search_space_size']})",
            module=ExperimentModule.BENCHMARKING,
            experiment_type="quantum_vs_classical_search",
            description=f"Comparison of Grover quadratic speedup against classical linear search for marked state |{marked_state}⟩",
            configuration=request.data,
            methodology_notes=result["scientific_notes"]["simulation_overhead_disclosure"],
            status=ExperimentStatus.SUCCEEDED,
            started_at=timezone.now(),
            completed_at=timezone.now()
        )

        # Persist Quantum BenchmarkRun
        BenchmarkRun.objects.create(
            experiment=exp,
            algorithm_name="Grover's Search",
            implementation_type="quantum",
            configuration={"marked_state": marked_state, "shots": shots, "seed": seed},
            raw_result={"counts": result["quantum"]["counts"]},
            solution_quality=result["quantum"]["success_probability"],
            execution_time_ms=result["quantum"]["execution_time_ms"],
            circuit_depth=result["quantum"]["circuit_depth"],
            gate_count=result["quantum"]["gate_count"]
        )

        # Persist Classical BenchmarkRun
        BenchmarkRun.objects.create(
            experiment=exp,
            algorithm_name="Classical Linear Search",
            implementation_type="classical",
            configuration={"search_space_size": result["search_space_size"], "target": marked_state},
            raw_result={"evaluations": result["classical"]["evaluations"]},
            solution_quality=1.0,
            execution_time_ms=result["classical"]["execution_time_ms"]
        )

        result["experiment_id"] = str(exp.id)
        return Response(result)

class BenchmarkListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        experiments = Experiment.objects.filter(module=ExperimentModule.BENCHMARKING).order_by('-created_at')[:10]
        data = [{
            "id": str(exp.id),
            "name": exp.name,
            "experiment_type": exp.experiment_type,
            "created_at": exp.created_at.isoformat()
        } for exp in experiments]
        return Response(data)
