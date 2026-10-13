from django.urls import path
from .views import BenchmarkRunView, BenchmarkListView

urlpatterns = [
    path('run/', BenchmarkRunView.as_view(), name='benchmark_run'),
    path('', BenchmarkListView.as_view(), name='benchmark_list'),
]
