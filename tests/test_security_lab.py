import json
from django.test import TestCase, Client
from apps.security_lab.models import SecurityAssessment
from quantum_engine.security.bb84 import simulate_bb84_protocol
from quantum_engine.security.pqc_inventory import assess_crypto_inventory

class Phase5QuantumSecurityLabTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_bb84_no_eavesdropper_secure_exchange(self):
        # 128 photons, Eve absent
        res = simulate_bb84_protocol(num_bits=128, eve_present=False, sample_ratio=0.5, seed=42)
        self.assertEqual(res["num_bits_sent"], 128)
        self.assertFalse(res["eve_present"])
        # In ideal noiseless channel with no eavesdropper, QBER should be 0.0
        self.assertEqual(res["qber"], 0.0)
        self.assertEqual(res["errors_detected"], 0)
        self.assertTrue(res["is_secure"])
        self.assertGreater(res["final_key_length"], 0)

    def test_bb84_intercept_resend_eve_attack_detection(self):
        # 256 photons, Eve present
        res = simulate_bb84_protocol(num_bits=256, eve_present=True, sample_ratio=0.5, seed=42)
        self.assertTrue(res["eve_present"])
        # Under intercept-resend attack, theoretical QBER is ~25%. Must clearly exceed 11% threshold
        self.assertGreater(res["qber"], 0.15)
        self.assertFalse(res["is_secure"])

    def test_pqc_inventory_classification_and_hndl(self):
        test_inventory = [
            {"system_name": "API TLS Session", "algorithm": "RSA-2048", "criticality": "Critical"},
            {"system_name": "Key Agreement", "algorithm": "ECDH X25519", "criticality": "High"},
            {"system_name": "Encrypted Database", "algorithm": "AES-256", "criticality": "High"}
        ]
        assessment = assess_crypto_inventory(test_inventory)
        self.assertEqual(assessment["total_assets"], 3)
        # RSA and ECDH are broken by Shor and susceptible to HNDL wiretapping
        self.assertGreaterEqual(assessment["critical_count"], 1)
        self.assertEqual(assessment["hndl_vulnerabilities"], 2)
        # AES-256 is quantum-resistant against Grover
        aes_asset = next(a for a in assessment["assessed_assets"] if "AES-256" in a["algorithm"])
        self.assertEqual(aes_asset["risk_level"], "Low")

    def test_security_api_endpoints_open_access(self):
        # Test BB84 API
        bb84_res = self.client.post(
            '/api/v1/security/bb84/run/',
            data=json.dumps({"num_bits": 64, "eve_present": False}),
            content_type='application/json'
        )
        self.assertEqual(bb84_res.status_code, 200)
        data = bb84_res.json()
        self.assertIn('assessment_id', data)
        self.assertTrue(SecurityAssessment.objects.filter(id=data['assessment_id']).exists())

        # Test PQC assessment API
        pqc_res = self.client.post(
            '/api/v1/security/pqc/assess/',
            data=json.dumps({"inventory_items": []}),
            content_type='application/json'
        )
        self.assertEqual(pqc_res.status_code, 200)
        pqc_data = pqc_res.json()
        self.assertIn('overall_posture', pqc_data)
        self.assertIn('assessed_assets', pqc_data)
