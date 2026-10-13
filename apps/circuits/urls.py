from django.urls import path
from .views import (
    CircuitListCreateView, CircuitDetailView, CircuitValidateView,
    CircuitSimulateView, CircuitExportView
)

urlpatterns = [
    path('', CircuitListCreateView.as_view(), name='circuit_list_create'),
    path('<uuid:pk>/', CircuitDetailView.as_view(), name='circuit_detail'),
    path('<uuid:pk>/validate/', CircuitValidateView.as_view(), name='circuit_validate'),
    path('<uuid:pk>/simulate/', CircuitSimulateView.as_view(), name='circuit_simulate'),
    path('<uuid:pk>/export/', CircuitExportView.as_view(), name='circuit_export'),
]
