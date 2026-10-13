import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.experiments.models import Experiment, ExperimentStatus, ExperimentModule
from apps.circuits.models import Circuit
from apps.audit.models import AuditEvent

class Phase1AccountAndDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "quantum_researcher"
        self.password = "Secur3Passw0rd!"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="researcher@qverse.org"
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            display_name="Dr. Quantum",
            research_interests="QKD, QAOA, Aer Simulation"
        )

    def test_csrf_token_endpoint(self):
        response = self.client.get('/api/v1/auth/csrf/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrfToken', response.json())

    def test_registration_and_audit(self):
        new_user_data = {
            "username": "alice_physicist",
            "password": "SuperStrongPassword123!",
            "email": "alice@lab.edu",
            "display_name": "Alice P.",
            "research_interests": "Entanglement and Grover"
        }
        response = self.client.post(
            '/api/v1/auth/register/',
            data=json.dumps(new_user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['username'], "alice_physicist")
        self.assertEqual(data['profile']['display_name'], "Alice P.")
        
        # Verify audit event logged
        audit = AuditEvent.objects.filter(action='USER_REGISTER').first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor.username, "alice_physicist")

    def test_login_and_logout(self):
        # Valid login
        login_res = self.client.post(
            '/api/v1/auth/login/',
            data=json.dumps({"username": self.username, "password": self.password}),
            content_type='application/json'
        )
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(login_res.json()['username'], self.username)

        # Authenticated /me endpoint
        me_res = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()['username'], self.username)

        # Logout
        logout_res = self.client.post('/api/v1/auth/logout/')
        self.assertEqual(logout_res.status_code, 200)

        # /me should now be unauthorized
        me_unauth = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_unauth.status_code, 403)

    def test_dashboard_summary_with_real_db_records(self):
        self.client.login(username=self.username, password=self.password)

        # Initial state should show 0 experiments
        res = self.client.get('/api/v1/dashboard/summary/')
        self.assertEqual(res.status_code, 200)
        summary = res.json()
        self.assertEqual(summary['metrics']['total_experiments'], 0)
        self.assertEqual(summary['metrics']['total_circuits'], 0)
        self.assertTrue(summary['simulator_status']['ready'])

        # Create real experiment and circuit
        Circuit.objects.create(
            owner=self.user,
            name="Bell State Circuit",
            num_qubits=2
        )
        Experiment.objects.create(
            owner=self.user,
            name="Bell State Verification",
            module=ExperimentModule.CIRCUIT_STUDIO,
            experiment_type="bell_state",
            status=ExperimentStatus.SUCCEEDED
        )

        res2 = self.client.get('/api/v1/dashboard/summary/')
        self.assertEqual(res2.status_code, 200)
        summary2 = res2.json()
        self.assertEqual(summary2['metrics']['total_experiments'], 1)
        self.assertEqual(summary2['metrics']['succeeded'], 1)
        self.assertEqual(summary2['metrics']['total_circuits'], 1)

        # Check recent experiments endpoint
        recent_res = self.client.get('/api/v1/dashboard/recent-experiments/')
        self.assertEqual(recent_res.status_code, 200)
        recent_data = recent_res.json()
        self.assertEqual(len(recent_data), 1)
        self.assertEqual(recent_data[0]['name'], "Bell State Verification")
