from datetime import datetime, timezone
import time
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckAPIView(APIView):
    """
    Health check endpoint for Docker, load balancers, and monitoring tools.
    Verifies database and cache service connectivity.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Application health check",
        description="Checks system readiness, database connectivity, and cache/redis status.",
        responses={
            200: inline_serializer(
                name='HealthCheckResponse',
                fields={
                    'status': serializers.CharField(),
                    'timestamp': serializers.CharField(),
                    'version': serializers.CharField(),
                    'services': serializers.DictField(),
                    'response_time_ms': serializers.FloatField(),
                }
            ),
            503: inline_serializer(
                name='HealthCheckErrorResponse',
                fields={
                    'status': serializers.CharField(),
                    'timestamp': serializers.CharField(),
                    'services': serializers.DictField(),
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        start_time = time.time()
        services = {}
        all_healthy = True

        # Check Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            services['database'] = {
                'status': 'healthy',
                'vendor': connection.vendor
            }
        except Exception as e:
            all_healthy = False
            services['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check Redis Cache
        try:
            cache_test_key = '__circlo_health_check__'
            cache.set(cache_test_key, 'ok', timeout=5)
            cache_value = cache.get(cache_test_key)
            if cache_value == 'ok':
                services['cache'] = {
                    'status': 'healthy',
                    'backend': cache.__class__.__name__
                }
            else:
                services['cache'] = {
                    'status': 'degraded',
                    'message': 'Cache write succeeded but read returned unexpected value'
                }
        except Exception as e:
            # Cache failure marks degraded rather than blocking full app in dev
            services['cache'] = {
                'status': 'unreachable',
                'error': str(e)
            }

        response_time = round((time.time() - start_time) * 1000, 2)
        payload = {
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'services': services,
            'response_time_ms': response_time,
        }

        # If critical service (database) is down, return HTTP 503
        if services.get('database', {}).get('status') == 'unhealthy':
            return Response(payload, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(payload, status=status.HTTP_200_OK)


class HomeView(View):
    """
    Renders the web application landing/base page.
    """
    def get(self, request):
        return render(request, 'base.html', {
            'title': 'Circlo - Connect, Share and Discover',
            'app_name': 'Circlo'
        })
