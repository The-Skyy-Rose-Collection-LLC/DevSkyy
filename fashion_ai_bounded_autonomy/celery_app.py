"""
Celery Application Configuration for Bounded Autonomy System

This module configures Celery for async task processing with Redis as the broker.
All tasks respect bounded autonomy principles:
- Tasks are logged and auditable
- High-risk operations still require human approval
- Tasks can be monitored and controlled

Redis Configuration:
- Broker: redis://localhost:6379/0
- Backend: redis://localhost:6379/1
- Visibility timeout: 3600s (1 hour)
"""

from celery import Celery
from kombu import Queue
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'fashion_ai_bounded_autonomy',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Celery Configuration
celery_app.conf.update(
    # Task execution
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task routing
    task_default_queue='bounded_autonomy_default',
    task_default_exchange='bounded_autonomy',
    task_default_routing_key='default',

    # Task result backend
    result_backend='redis://localhost:6379/1',
    result_expires=86400,  # Results expire after 24 hours

    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Task time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit

    # Task acknowledgment
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Visibility timeout
    broker_transport_options={'visibility_timeout': 3600},  # 1 hour

    #Beat schedule (periodic tasks)
    beat_schedule={
        'generate-daily-reports': {
            'task': 'fashion_ai_bounded_autonomy.tasks.generate_daily_reports_task',
            'schedule': 86400.0,  # Every 24 hours
        },
        'cleanup-expired-approvals': {
            'task': 'fashion_ai_bounded_autonomy.tasks.cleanup_expired_approvals_task',
            'schedule': 3600.0,  # Every hour
        },
        'monitor-agent-health': {
            'task': 'fashion_ai_bounded_autonomy.tasks.monitor_agent_health_task',
            'schedule': 300.0,  # Every 5 minutes
        },
        'performance-metrics-snapshot': {
            'task': 'fashion_ai_bounded_autonomy.tasks.performance_snapshot_task',
            'schedule': 900.0,  # Every 15 minutes
        },
    },

    # Task queues
    task_queues=(
        Queue('bounded_autonomy_default', routing_key='default'),
        Queue('bounded_autonomy_high_priority', routing_key='high_priority'),
        Queue('bounded_autonomy_reports', routing_key='reports'),
        Queue('bounded_autonomy_monitoring', routing_key='monitoring'),
        Queue('bounded_autonomy_data_processing', routing_key='data_processing'),
    ),

    # Task routes
    task_routes={
        'fashion_ai_bounded_autonomy.tasks.send_approval_notification_task': {
            'queue': 'bounded_autonomy_high_priority',
            'routing_key': 'high_priority',
        },
        'fashion_ai_bounded_autonomy.tasks.generate_*': {
            'queue': 'bounded_autonomy_reports',
            'routing_key': 'reports',
        },
        'fashion_ai_bounded_autonomy.tasks.monitor_*': {
            'queue': 'bounded_autonomy_monitoring',
            'routing_key': 'monitoring',
        },
        'fashion_ai_bounded_autonomy.tasks.process_data_*': {
            'queue': 'bounded_autonomy_data_processing',
            'routing_key': 'data_processing',
        },
    },
)

# Auto-discover tasks from tasks.py
celery_app.autodiscover_tasks(['fashion_ai_bounded_autonomy'])

logger.info("✅ Celery app configured for bounded autonomy system")
