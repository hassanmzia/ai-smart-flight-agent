from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentSessionViewSet,
    AgentExecutionViewSet,
    AgentLogViewSet,
    plan_travel,
    chat
)

app_name = 'agents'

router = DefaultRouter()
router.register(r'sessions', AgentSessionViewSet, basename='session')
router.register(r'executions', AgentExecutionViewSet, basename='execution')
router.register(r'logs', AgentLogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
    path('plan', plan_travel, name='plan_travel'),
    path('chat', chat, name='chat'),
]
