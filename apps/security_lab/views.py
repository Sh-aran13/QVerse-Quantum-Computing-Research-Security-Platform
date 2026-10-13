from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.accounts.open_access import get_or_create_open_researcher
from apps.security_lab.models import SecurityAssessment
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from quantum_engine.security.bb84 import simulate_bb84_protocol
from quantum_engine.security.pqc_inventory import assess_crypto_inventory, ALGORITHM_TAXONOMY

class BB84SimulateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_or_create_open_researcher(request)
        num_bits = int(request.data.get('num_bits', 64))
        eve_present = bool(request.data.get('eve_present', False))
        sample_ratio = float(request.data.get('sample_ratio', 0.5))
        seed = request.data.get('seed')
        if seed is not None:
            seed = int(seed)

        try:
            result = simulate_bb84_protocol(
                num_bits=num_bits,
                eve_present=eve_present,
                sample_ratio=sample_ratio,
                seed=seed
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Persist as SecurityAssessment
        assessment = SecurityAssessment.objects.create(
            owner=user,
            assessment_type="bb84_simulation",
            configuration={
                "num_bits": num_bits,
                "eve_present": eve_present,
                "sample_ratio": sample_ratio,
                "seed": seed
            },
            result_data=result,
            risk_summary=f"BB84 QBER: {result['qber_percentage']}% (Eve: {'Detected' if (eve_present and not result['is_secure']) else 'None'}). Status: {'SECURE' if result['is_secure'] else 'ABORT_INTRUSION'}"
        )
        result["assessment_id"] = str(assessment.id)
        return Response(result)

class PQCAssessmentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = get_or_create_open_researcher(request)
        inventory = request.data.get('inventory_items', [])
        if not inventory or not isinstance(inventory, list):
            # Provide sample production inventory if none sent
            inventory = [
                {"system_name": "Web Gateway TLS 1.3", "algorithm": "ECDH (X25519)", "criticality": "Critical"},
                {"system_name": "Identity Auth Token", "algorithm": "RSA-2048", "criticality": "High"},
                {"system_name": "Database at Rest", "algorithm": "AES-256-GCM", "criticality": "High"},
                {"system_name": "API Code Signatures", "algorithm": "ECDSA P-256", "criticality": "Medium"}
            ]

        assessment_result = assess_crypto_inventory(inventory)

        # Persist as SecurityAssessment
        assessment = SecurityAssessment.objects.create(
            owner=user,
            assessment_type="pqc_inventory",
            configuration={"items_count": len(inventory)},
            result_data=assessment_result,
            risk_summary=f"Posture: {assessment_result['overall_posture']} (Critical: {assessment_result['critical_count']}, HNDL: {assessment_result['hndl_vulnerabilities']})"
        )
        assessment_result["assessment_id"] = str(assessment.id)
        return Response(assessment_result)

class SecurityAssessmentsListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        assessments = SecurityAssessment.objects.all().order_by('-created_at')[:10]
        data = [{
            "id": str(a.id),
            "assessment_type": a.assessment_type,
            "risk_summary": a.risk_summary,
            "created_at": a.created_at.isoformat()
        } for a in assessments]
        return Response(data)

class PQCReferenceTaxonomyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(ALGORITHM_TAXONOMY)
