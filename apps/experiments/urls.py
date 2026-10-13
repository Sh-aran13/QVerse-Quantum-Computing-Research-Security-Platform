from django.urls import path
from .views import ExperimentListCreateView, ExperimentDetailView, ExperimentCancelView

urlpatterns = [
    path('', ExperimentListCreateView.as_view(), name='experiment_list_create'),
    path('<uuid:pk>/', ExperimentDetailView.as_view(), name='experiment_detail'),
    path('<uuid:pk>/cancel/', ExperimentCancelView.as_view(), name='experiment_cancel'),
    path('<uuid:pk>/results/', ExperimentDetailView.as_view(), name='experiment_results'),
]
