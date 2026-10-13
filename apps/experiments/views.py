from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentResult

class ExperimentListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        experiments = Experiment.objects.all().order_by('-created_at')
        module = request.query_params.get('module')
        if module:
            experiments = experiments.filter(module=module)
        status_filter = request.query_params.get('status')
        if status_filter:
            experiments = experiments.filter(status=status_filter)

        data = [{
            "id": str(e.id),
            "name": e.name,
            "module": e.module,
            "experiment_type": e.experiment_type,
            "description": e.description,
            "status": e.status,
            "created_at": e.created_at.isoformat(),
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            "has_result": hasattr(e, 'result')
        } for e in experiments]
        return Response(data)

    def post(self, request):
        user = get_or_create_open_researcher(request)
        name = request.data.get('name', 'Custom Quantum Experiment')
        module = request.data.get('module', 'CIRCUIT_STUDIO')
        exp_type = request.data.get('experiment_type', 'general')
        desc = request.data.get('description', '')
        config = request.data.get('configuration', {})
        notes = request.data.get('methodology_notes', '')

        exp = Experiment.objects.create(
            owner=user,
            name=name,
            module=module,
            experiment_type=exp_type,
            description=desc,
            configuration=config,
            methodology_notes=notes,
            status=ExperimentStatus.SUCCEEDED,
            started_at=timezone.now(),
            completed_at=timezone.now()
        )
        return Response({"id": str(exp.id), "name": exp.name, "status": exp.status}, status=status.HTTP_201_CREATED)

class ExperimentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        result_data = None
        metrics = None
        if hasattr(exp, 'result'):
            result_data = exp.result.result_data
            metrics = exp.result.metrics

        return Response({
            "id": str(exp.id),
            "name": exp.name,
            "module": exp.module,
            "experiment_type": exp.experiment_type,
            "description": exp.description,
            "configuration": exp.configuration,
            "methodology_notes": exp.methodology_notes,
            "status": exp.status,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "result": {
                "data": result_data,
                "metrics": metrics
            } if result_data else None
        })

    def delete(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        exp.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ExperimentCancelView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        if exp.status in [ExperimentStatus.PENDING, ExperimentStatus.RUNNING]:
            exp.status = ExperimentStatus.CANCELLED
            exp.save()
            return Response({"status": "CANCELLED"})
        return Response({"message": f"Experiment cannot be cancelled from status {exp.status}"})
