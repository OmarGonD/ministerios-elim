from django.db.models import F
from django.utils import timezone

from .models import EngagementMetric


def record_metric(event_type, label=''):
    """Increment an aggregate daily counter. No user data is stored."""
    label = str(label or '')[:160]
    metric, created = EngagementMetric.objects.get_or_create(
        date=timezone.localdate(),
        event_type=event_type,
        label=label,
        defaults={'count': 1},
    )
    if not created:
        EngagementMetric.objects.filter(pk=metric.pk).update(count=F('count') + 1)
