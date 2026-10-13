from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count, Q
import qiskit
import qiskit_aer

from apps.accounts.open_access import get_or_create_open_researcher
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from apps.circuits.models import Circuit

class DashboardSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = get_or_create_open_researcher(request)
        user_experiments = Experiment.objects.all()
        
        total = user_experiments.count()
        succeeded = user_experiments.filter(status=ExperimentStatus.SUCCEEDED).count()
        failed = user_experiments.filter(status=ExperimentStatus.FAILED).count()
        running = user_experiments.filter(status=ExperimentStatus.RUNNING).count()
        pending = user_experiments.filter(status=ExperimentStatus.PENDING).count()
        circuits_count = Circuit.objects.count()

        by_module = (
            user_experiments
            .values('module')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return Response({
            "metrics": {
                "total_experiments": total,
                "succeeded": succeeded,
                "failed": failed,
                "running": running,
                "pending": pending,
                "total_circuits": circuits_count
            },
            "by_module": list(by_module),
            "simulator_status": {
                "engine": "Qiskit Aer Simulator",
                "ready": True,
                "qiskit_version": qiskit.__version__,
                "qiskit_aer_version": qiskit_aer.__version__,
                "hardware_connected": False
            }
        })

class RecentExperimentsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        recent = Experiment.objects.all().order_by('-created_at')[:8]
        
        data = [{
            "id": str(exp.id),
            "name": exp.name,
            "module": exp.get_module_display(),
            "experiment_type": exp.experiment_type,
            "status": exp.status,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None
        } for exp in recent]

        return Response(data)

class ModuleStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        modules = [
            {"id": "circuits", "name": "Quantum Circuit Studio", "status": "Ready", "phase": "Phase 2"},
            {"id": "algorithms", "name": "Quantum Algorithms Lab", "status": "Ready", "phase": "Phase 3"},
            {"id": "benchmarking", "name": "Quantum vs Classical Benchmarking", "status": "Ready", "phase": "Phase 4"},
            {"id": "security", "name": "Quantum Security Lab", "status": "Ready", "phase": "Phase 5"},
            {"id": "optimization", "name": "Quantum Optimization Lab", "status": "Ready", "phase": "Phase 6"},
            {"id": "quantum_ml", "name": "Hybrid Quantum AI Lab", "status": "Ready", "phase": "Phase 6"},
            {"id": "circuit_optimizer", "name": "Quantum Circuit Optimizer", "status": "Ready", "phase": "Phase 4"},
            {"id": "experiments", "name": "Experiment Manager", "status": "Ready", "phase": "Phase 7"}
        ]
        return Response(modules)
