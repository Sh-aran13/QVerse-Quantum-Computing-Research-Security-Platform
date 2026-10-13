import uuid
from django.db import models
from django.contrib.auth.models import User

class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_events')
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    request_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'system'
        return f"{self.timestamp} - {actor_name} - {self.action} on {self.resource_type}"
