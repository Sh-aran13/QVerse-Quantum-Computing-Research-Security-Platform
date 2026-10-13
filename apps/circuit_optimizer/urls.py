from django.urls import path
from .views import CircuitAnalyzeView, CircuitOptimizeView

urlpatterns = [
    path('analyze/', CircuitAnalyzeView.as_view(), name='circuit_analyze'),
    path('optimize/', CircuitOptimizeView.as_view(), name='circuit_optimize'),
    path('compare/', CircuitOptimizeView.as_view(), name='circuit_compare'),
]
