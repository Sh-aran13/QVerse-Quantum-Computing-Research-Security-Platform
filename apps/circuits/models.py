import uuid
from django.db import models
from django.contrib.auth.models import User

class Circuit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circuits')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    num_qubits = models.PositiveSmallIntegerField(default=2)
    num_classical_bits = models.PositiveSmallIntegerField(default=2)
    circuit_definition = models.JSONField(
        default=dict,
        help_text="Validated JSON representation of gates and measurements"
    )
    circuit_qasm = models.TextField(blank=True, help_text="Generated OpenQASM representation")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.num_qubits} qubits)"
