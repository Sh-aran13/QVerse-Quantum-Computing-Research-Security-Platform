from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Circuit
from .serializers import CircuitSerializer, CircuitSimulateRequestSerializer
from apps.accounts.open_access import get_or_create_open_researcher
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule, ExperimentResult
from apps.audit.models import AuditEvent
from quantum_engine.circuit_builder import validate_circuit_definition, CircuitValidationError, build_qiskit_circuit, export_to_qasm
from quantum_engine.simulator import CircuitSimulator

class CircuitListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        circuits = Circuit.objects.all()
        serializer = CircuitSerializer(circuits, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = get_or_create_open_researcher(request)
        serializer = CircuitSerializer(data=request.data)
        if serializer.is_valid():
            definition = serializer.validated_data.get('circuit_definition', {})
            qasm_str = ""
            if definition and definition.get('operations'):
                try:
                    qc = build_qiskit_circuit(definition)
                    qasm_str = export_to_qasm(qc)
                except Exception:
                    pass
            
            circuit = serializer.save(owner=user, circuit_qasm=qasm_str)
            return Response(CircuitSerializer(circuit).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CircuitDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(Circuit, pk=pk)

    def get(self, request, pk):
        circuit = self.get_object(pk)
        return Response(CircuitSerializer(circuit).data)

    def patch(self, request, pk):
        circuit = self.get_object(pk)
        serializer = CircuitSerializer(circuit, data=request.data, partial=True)
        if serializer.is_valid():
            definition = serializer.validated_data.get('circuit_definition', circuit.circuit_definition)
            if definition and definition.get('operations'):
                try:
                    qc = build_qiskit_circuit(definition)
                    serializer.validated_data['circuit_qasm'] = export_to_qasm(qc)
                except Exception:
                    pass
            circuit = serializer.save()
            return Response(CircuitSerializer(circuit).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        circuit = self.get_object(pk)
        circuit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CircuitValidateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        circuit = get_object_or_404(Circuit, pk=pk)
        try:
            validate_circuit_definition(circuit.circuit_definition)
            return Response({
                "valid": True,
                "message": "Circuit structure is valid and compatible with Qiskit Aer."
            })
        except CircuitValidationError as e:
            return Response({
                "valid": False,
                "error": e.message,
                "details": e.details
            }, status=status.HTTP_400_BAD_REQUEST)

class CircuitSimulateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        user = get_or_create_open_researcher(request)
        circuit = get_object_or_404(Circuit, pk=pk)
        req_serializer = CircuitSimulateRequestSerializer(data=request.data)
        if not req_serializer.is_valid():
            return Response(req_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        shots = req_serializer.validated_data['shots']
        seed = req_serializer.validated_data.get('seed')
        include_statevector = req_serializer.validated_data.get('include_statevector', False)
        save_as_exp = req_serializer.validated_data.get('save_as_experiment', True)
        exp_name = req_serializer.validated_data.get('experiment_name') or f"Sim: {circuit.name}"

        # Execute on local Qiskit Aer simulator
        simulator = CircuitSimulator()
        try:
            sim_output = simulator.simulate(
                circuit.circuit_definition,
                shots=shots,
                seed=seed,
                include_statevector=include_statevector
            )
        except Exception as e:
            return Response({
                "error": {
                    "code": "SIMULATION_FAILED",
                    "message": f"Quantum simulation error: {str(e)}"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        experiment_id = None
        if save_as_exp:
            exp = Experiment.objects.create(
                owner=user,
                name=exp_name,
                module=ExperimentModule.CIRCUIT_STUDIO,
                experiment_type="circuit_simulation",
                description=f"Simulation of circuit '{circuit.name}' ({circuit.num_qubits} qubits, {shots} shots)",
                configuration={
                    "circuit_id": str(circuit.id),
                    "shots": shots,
                    "seed": seed,
                    "include_statevector": include_statevector
                },
                methodology_notes="Execution completed on local Qiskit Aer simulator with finite-shot statistics.",
                status=ExperimentStatus.SUCCEEDED,
                started_at=timezone.now(),
                completed_at=timezone.now()
            )
            ExperimentResult.objects.create(
                experiment=exp,
                result_data={
                    "counts": sim_output["counts"],
                    "probabilities": sim_output["probabilities"],
                    "statevector": sim_output.get("statevector")
                },
                metrics=sim_output["metrics"],
                backend_name=sim_output["metrics"]["backend_name"],
                backend_version=sim_output["metrics"]["backend_version"],
                shots=shots,
                seed=seed,
                execution_time_ms=sim_output["metrics"]["execution_time_ms"],
                circuit_depth=sim_output["metrics"]["circuit_depth"],
                gate_count=sim_output["metrics"]["gate_count"],
                qubit_count=sim_output["metrics"]["qubit_count"]
            )
            experiment_id = str(exp.id)

        sim_output["experiment_id"] = experiment_id
        return Response(sim_output)

class CircuitExportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        circuit = get_object_or_404(Circuit, pk=pk)
        try:
            qc = build_qiskit_circuit(circuit.circuit_definition)
            qasm_str = export_to_qasm(qc)
        except Exception as e:
            qasm_str = circuit.circuit_qasm or f"// QASM export failed: {str(e)}"

        return Response({
            "circuit_id": str(circuit.id),
            "name": circuit.name,
            "qasm": qasm_str,
            "json": circuit.circuit_definition
        })
