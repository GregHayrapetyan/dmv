"""Lightweight health check for load balancers and container probes."""

from django.db import connection
from django.http import JsonResponse


def health(_request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False

    status = 200 if db_ok else 503
    return JsonResponse(
        {
            "success": db_ok,
            "error": None if db_ok else "database unavailable",
            "data": {"status": "ok" if db_ok else "degraded", "database": db_ok},
        },
        status=status,
    )
