from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='dashboard/index.html'), name='home'),
    path('circuits/', TemplateView.as_view(template_name='circuits/index.html'), name='circuits_studio'),
    path('algorithms/', TemplateView.as_view(template_name='algorithms/index.html'), name='algorithms_lab'),
    path('benchmarking/', TemplateView.as_view(template_name='benchmarking/index.html'), name='benchmarking_lab'),
    path('circuit-optimizer/', TemplateView.as_view(template_name='circuit_optimizer/index.html'), name='circuit_optimizer_lab'),
    path('security/', TemplateView.as_view(template_name='security/index.html'), name='security_lab'),
    path('optimization/', TemplateView.as_view(template_name='optimization/index.html'), name='optimization_lab'),
    path('quantum-ml/', TemplateView.as_view(template_name='quantum_ml/index.html'), name='quantum_ml_lab'),
    path('experiments/', TemplateView.as_view(template_name='experiments/index.html'), name='experiments_manager'),
    path('reports/', TemplateView.as_view(template_name='experiments/index.html'), name='reports_page'),
]
