import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from compiler.pipeline import run_all


def index(request):
    return render(request, "analyzer/index.html")


@require_http_methods(["POST"])
def analyze(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponseBadRequest("Invalid JSON")

    source = payload.get("source", "")
    if not isinstance(source, str):
        return HttpResponseBadRequest("'source' must be a string")

    return JsonResponse(run_all(source))
