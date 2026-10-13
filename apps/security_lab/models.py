import uuid
from django.db import models
from django.contrib.auth.models import User

class SecurityAssessment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_assessments')
    assessment_type = models.CharField(max_length=50, help_text="'bb84_simulation' or 'pqc_inventory'")
    configuration = models.JSONField(default=dict)
    result_data = models.JSONField(default=dict)
    risk_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
