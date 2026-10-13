import csv
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from apps.experiments.models import Experiment

class ExportJSONView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        result_payload = {}
        if hasattr(exp, 'result'):
            result_payload = {
                "result_data": exp.result.result_data,
                "metrics": exp.result.metrics,
                "shots": exp.result.shots,
                "execution_time_ms": exp.result.execution_time_ms
            }

        data = {
            "platform": "QVerse Quantum Computing & Security Platform",
            "experiment_id": str(exp.id),
            "name": exp.name,
            "module": exp.module,
            "experiment_type": exp.experiment_type,
            "status": exp.status,
            "created_at": exp.created_at.isoformat(),
            "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
            "configuration": exp.configuration,
            "methodology_notes": exp.methodology_notes,
            "results": result_payload
        }
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="qverse_experiment_{exp.id}.json"'
        return response

class ExportCSVView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="qverse_experiment_{exp.id}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Experiment ID', str(exp.id)])
        writer.writerow(['Name', exp.name])
        writer.writerow(['Module', exp.module])
        writer.writerow(['Status', exp.status])
        writer.writerow(['Created At', exp.created_at.isoformat()])

        if hasattr(exp, 'result'):
            writer.writerow(['Backend Name', exp.result.backend_name])
            writer.writerow(['Shots', exp.result.shots])
            writer.writerow(['Execution Time (ms)', exp.result.execution_time_ms])
            writer.writerow(['Circuit Depth', exp.result.circuit_depth])
            writer.writerow(['Gate Count', exp.result.gate_count])
            writer.writerow(['Qubit Count', exp.result.qubit_count])

            counts = exp.result.result_data.get('counts', {})
            writer.writerow([])
            writer.writerow(['Bitstring', 'Measurement Count'])
            for bitstr, count in counts.items():
                writer.writerow([bitstr, count])

        return response

class ExportReportView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        exp = get_object_or_404(Experiment, pk=pk)
        # Research HTML Report Document
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>QVerse Scientific Experiment Report: {exp.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1e293b; padding: 2.5rem; max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #0f172a; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; }}
        .badge {{ background: #e0f2fe; color: #0369a1; padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: 600; font-size: 0.85rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 0.6rem 0.8rem; text-align: left; font-size: 0.9rem; }}
        th {{ background: #f8fafc; color: #475569; }}
        .callout {{ background: #f1f5f9; border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 4px; margin: 1rem 0; }}
    </style>
</head>
<body>
    <h1>QVerse Academic Experiment Report</h1>
    <p><span class="badge">{exp.module}</span> | <strong>Status:</strong> {exp.status} | <strong>ID:</strong> {exp.id}</p>
    
    <h2>1. Experiment Metadata</h2>
    <table>
        <tr><th>Experiment Name</th><td>{exp.name}</td></tr>
        <tr><th>Domain Module</th><td>{exp.module}</td></tr>
        <tr><th>Execution Type</th><td>{exp.experiment_type}</td></tr>
        <tr><th>Timestamp</th><td>{exp.created_at.isoformat()}</td></tr>
    </table>

    <h2>2. Methodology & Scientific Assumptions</h2>
    <div class="callout">
        {exp.methodology_notes or 'Executed on verified local quantum simulator (Qiskit Aer). Runtimes reflect classical CPU matrix operations.'}
    </div>

    <h2>3. Experimental Parameters</h2>
    <pre style="background: #f8fafc; padding: 1rem; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.85rem;">{json.dumps(exp.configuration, indent=2)}</pre>

    <footer style="margin-top: 3rem; border-top: 1px solid #e2e8f0; padding-top: 1rem; font-size: 0.8rem; color: #64748b;">
        Generated by QVerse Quantum Computing Research & Security Platform — B.Tech Major Project Edition.
    </footer>
</body>
</html>"""
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="qverse_report_{exp.id}.html"'
        return response
