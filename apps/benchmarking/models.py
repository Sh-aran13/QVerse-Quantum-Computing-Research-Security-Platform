import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.experiments.models import Experiment

class BenchmarkRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='benchmark_runs')
    algorithm_name = models.CharField(max_length=100)
    implementation_type = models.CharField(max_length=50, help_text="'quantum' or 'classical'")
    configuration = models.JSONField(default=dict)
    raw_result = models.JSONField(default=dict)
    solution_quality = models.FloatField(null=True, blank=True)
    execution_time_ms = models.FloatField()
    memory_usage_bytes = models.BigIntegerField(null=True, blank=True)
    circuit_depth = models.PositiveIntegerField(null=True, blank=True)
    gate_count = models.PositiveIntegerField(null=True, blank=True)
    noise_configuration = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
