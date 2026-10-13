from django.urls import path
from .views import (
    BB84SimulateView, PQCAssessmentView, SecurityAssessmentsListView,
    PQCReferenceTaxonomyView
)

urlpatterns = [
    path('bb84/run/', BB84SimulateView.as_view(), name='bb84_run'),
    path('assessments/', SecurityAssessmentsListView.as_view(), name='security_assessments_list'),
    path('pqc/assess/', PQCAssessmentView.as_view(), name='pqc_assess'),
    path('pqc/inventory/', PQCAssessmentView.as_view(), name='pqc_inventory'),
    path('pqc/taxonomy/', PQCReferenceTaxonomyView.as_view(), name='pqc_taxonomy'),
]
