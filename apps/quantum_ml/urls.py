from django.urls import path
from .views import QuantumMLExperimentView

urlpatterns = [
    path('experiments/', QuantumMLExperimentView.as_view(), name='qml_experiments'),
    path('run/', QuantumMLExperimentView.as_view(), name='qml_run'),
]
