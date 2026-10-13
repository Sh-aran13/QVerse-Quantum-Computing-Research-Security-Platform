import uuid
from django.db import models
from apps.experiments.models import Experiment

class QuantumMLRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.OneToOneField(Experiment, on_delete=models.CASCADE, related_name='qml_run')
    dataset_metadata = models.JSONField(default=dict)
    model_configuration = models.JSONField(default=dict)
    training_metrics = models.JSONField(default=dict)
    evaluation_metrics = models.JSONField(default=dict)
    random_seed = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
