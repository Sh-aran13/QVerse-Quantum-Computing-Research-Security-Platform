from django.urls import path
from .views import DashboardSummaryView, RecentExperimentsView, ModuleStatusView

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('recent-experiments/', RecentExperimentsView.as_view(), name='dashboard_recent'),
    path('module-status/', ModuleStatusView.as_view(), name='dashboard_modules'),
]
