"""
One-time backfill: promote legacy ContentItem rows to 'approved'.

Earlier moderation thresholds were strict (score > 0.7 → approved),
so most user submissions landed in 'pending' or 'rejected' and were
invisible on Explore/Trending. We've relaxed the rule, but existing
rows still need to be moved so the user's old submissions show up.

We only update rows that are currently pending/rejected — approved
and flagged rows are left alone.
"""
from django.db import migrations


def approve_legacy_content(apps, schema_editor):
    ContentItem = apps.get_model('agents', 'ContentItem')
    ContentItem.objects.filter(status__in=['pending', 'rejected']).update(
        status='approved',
    )


def noop_reverse(apps, schema_editor):
    # Can't know which rows were originally pending vs rejected after
    # we merged them; a no-op reverse is the safest choice.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('agents', '0006_contentitem_comments_count_and_more'),
    ]

    operations = [
        migrations.RunPython(approve_legacy_content, noop_reverse),
    ]
