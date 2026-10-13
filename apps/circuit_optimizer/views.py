from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.circuits.models import Circuit
from quantum_engine.transpilation import analyze_circuit_structure, optimize_quantum_circuit
from apps.accounts.open_access import get_or_create_open_researcher

class CircuitAnalyzeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        definition = request.data.get('circuit_definition')
        circuit_id = request.data.get('circuit_id')
        if not definition and circuit_id:
            try:
                circuit = Circuit.objects.get(id=circuit_id)
                definition = circuit.circuit_definition
            except Circuit.DoesNotExist:
                return Response({"error": "Circuit not found"}, status=status.HTTP_404_NOT_FOUND)

        if not definition:
            return Response({"error": "Circuit definition or circuit_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            analysis = analyze_circuit_structure(definition)
            return Response(analysis)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CircuitOptimizeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        definition = request.data.get('circuit_definition')
        circuit_id = request.data.get('circuit_id')
        opt_level = int(request.data.get('optimization_level', 2))
        basis_gates = request.data.get('basis_gates')

        if not definition and circuit_id:
            try:
                circuit = Circuit.objects.get(id=circuit_id)
                definition = circuit.circuit_definition
            except Circuit.DoesNotExist:
                return Response({"error": "Circuit not found"}, status=status.HTTP_404_NOT_FOUND)

        if not definition:
            return Response({"error": "Circuit definition or circuit_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = optimize_quantum_circuit(definition, optimization_level=opt_level, basis_gates=basis_gates)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
