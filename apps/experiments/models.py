import uuid
from django.db import models
from django.contrib.auth.models import User

class ExperimentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    RUNNING = 'RUNNING', 'Running'
    SUCCEEDED = 'SUCCEEDED', 'Succeeded'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ExperimentModule(models.TextChoices):
    CIRCUIT_STUDIO = 'CIRCUIT_STUDIO', 'Quantum Circuit Studio'
    ALGORITHMS = 'ALGORITHMS', 'Quantum Algorithms Lab'
    BENCHMARKING = 'BENCHMARKING', 'Quantum vs Classical Benchmarking'
    SECURITY_LAB = 'SECURITY_LAB', 'Quantum Security Lab'
    OPTIMIZATION = 'OPTIMIZATION', 'Quantum Optimization Lab'
    QUANTUM_ML = 'QUANTUM_ML', 'Hybrid Quantum AI Lab'
    CIRCUIT_OPTIMIZER = 'CIRCUIT_OPTIMIZER', 'Quantum Circuit Optimizer'

class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiments', db_index=True)
    name = models.CharField(max_length=255)
    module = models.CharField(max_length=50, choices=ExperimentModule.choices, db_index=True)
    experiment_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    configuration = models.JSONField(default=dict)
    methodology_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExperimentStatus.choices,
        default=ExperimentStatus.PENDING,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    error_summary = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.module}] {self.name} ({self.status})"

class ExperimentJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name='job')
    status = models.CharField(
        max_length=20,
        choices=ExperimentStatus.choices,
        default=ExperimentStatus.PENDING
    )
    attempt_count = models.PositiveSmallIntegerField(default=0)
    worker_identifier = models.CharField(max_length=100, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class ExperimentResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name='result')
    result_data = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    backend_name = models.CharField(max_length=100, default='qasm_simulator')
    backend_version = models.CharField(max_length=50, blank=True)
    shots = models.PositiveIntegerField(null=True, blank=True)
    seed = models.BigIntegerField(null=True, blank=True)
    execution_time_ms = models.FloatField(null=True, blank=True)
    circuit_depth = models.PositiveIntegerField(null=True, blank=True)
    gate_count = models.PositiveIntegerField(null=True, blank=True)
    qubit_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
