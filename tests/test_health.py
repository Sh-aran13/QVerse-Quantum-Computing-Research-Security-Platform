from django.test import TestCase, Client
from django.urls import reverse

class HealthCheckTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertIn('quantum_engine', data)
        self.assertTrue(data['quantum_engine'].get('simulator_ready'))
        self.assertIn('qiskit_version', data['quantum_engine'])
        self.assertIn('qiskit_aer_version', data['quantum_engine'])

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
