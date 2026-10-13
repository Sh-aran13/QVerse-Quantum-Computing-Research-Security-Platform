from django.urls import path
from .views import AlgorithmListView, AlgorithmMetadataView, AlgorithmRunView

urlpatterns = [
    path('', AlgorithmListView.as_view(), name='algorithm_list'),
    path('<str:algorithm>/metadata/', AlgorithmMetadataView.as_view(), name='algorithm_metadata'),
    path('<str:algorithm>/run/', AlgorithmRunView.as_view(), name='algorithm_run'),
]
