import uuid
from django.db import models
from apps.experiments.models import Experiment

class OptimizationRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name='optimization_run')
    problem_definition = models.JSONField(default=dict)
    algorithm_configuration = models.JSONField(default=dict)
    best_solution = models.CharField(max_length=255, blank=True)
    objective_value = models.FloatField(null=True, blank=True)
    convergence_history = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
