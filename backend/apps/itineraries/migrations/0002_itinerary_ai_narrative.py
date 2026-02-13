from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineraries', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='itinerary',
            name='ai_narrative',
            field=models.TextField(blank=True, default='', help_text='Full AI-generated day-by-day narrative for PDF export'),
        ),
    ]
