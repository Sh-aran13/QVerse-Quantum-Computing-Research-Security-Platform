from django.urls import path
from .views import QAOARunView

urlpatterns = [
    path('qaoa/run/', QAOARunView.as_view(), name='qaoa_run'),
    path('run/', QAOARunView.as_view(), name='optimization_run'),
]
