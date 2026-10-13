from django.urls import path
from .views import ExportJSONView, ExportCSVView, ExportReportView

urlpatterns = [
    path('<uuid:pk>/export/json/', ExportJSONView.as_view(), name='export_json'),
    path('<uuid:pk>/export/csv/', ExportCSVView.as_view(), name='export_csv'),
    path('<uuid:pk>/export/report/', ExportReportView.as_view(), name='export_report'),
]
