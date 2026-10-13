import json
from rest_framework import serializers
from .models import Circuit
from quantum_engine.circuit_builder import validate_circuit_definition, CircuitValidationError

class CircuitSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Circuit
        fields = [
            'id', 'owner', 'owner_username', 'name', 'description',
            'num_qubits', 'num_classical_bits', 'circuit_definition',
            'circuit_qasm', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def validate_circuit_definition(self, value):
        if not value:
            return value
        try:
            validate_circuit_definition(value)
        except CircuitValidationError as e:
            raise serializers.ValidationError(e.message)
        return value

class CircuitSimulateRequestSerializer(serializers.Serializer):
    shots = serializers.IntegerField(default=1024, min_value=1, max_value=10000)
    seed = serializers.IntegerField(required=False, allow_null=True)
    include_statevector = serializers.BooleanField(default=False)
    save_as_experiment = serializers.BooleanField(default=True)
    experiment_name = serializers.CharField(required=False, max_length=255)
