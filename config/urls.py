"""
QVerse URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
import qiskit
import qiskit_aer

def health_check(request):
    """System health check endpoint reporting simulator & service readiness."""
    return JsonResponse({
        "status": "healthy",
        "service": "QVerse Quantum Computing & Security Platform",
        "environment": "active",
        "quantum_engine": {
            "qiskit_version": qiskit.__version__,
            "qiskit_aer_version": qiskit_aer.__version__,
            "simulator_ready": True
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health/', health_check, name='health_check'),
    
    # App routers
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/dashboard/', include('apps.dashboard.urls')),
    path('api/v1/circuits/', include('apps.circuits.urls')),
    path('api/v1/algorithms/', include('apps.algorithms.urls')),
    path('api/v1/benchmarks/', include('apps.benchmarking.urls')),
    path('api/v1/security/', include('apps.security_lab.urls')),
    path('api/v1/optimization/', include('apps.optimization.urls')),
    path('api/v1/quantum-ml/', include('apps.quantum_ml.urls')),
    path('api/v1/circuit-optimizer/', include('apps.circuit_optimizer.urls')),
    path('api/v1/experiments/', include('apps.experiments.urls')),
    path('api/v1/experiments/', include('apps.reports.urls')),
    path('api/v1/reports/', include('apps.reports.urls')),
    
    # Template UI Views
    path('', include('apps.dashboard.ui_urls')),
]
