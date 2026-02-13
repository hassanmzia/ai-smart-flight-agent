from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('itineraries', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itinerary',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('planned', 'Planned'),
                    ('approved', 'Approved'),
                    ('booking', 'Booking in Progress'),
                    ('booked', 'Booked'),
                    ('active', 'Active'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                max_length=20,
            ),
        ),
    ]
