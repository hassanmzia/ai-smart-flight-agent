# Generated migration for User model

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('phone_number', models.CharField(blank=True, max_length=20, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')])),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
                'ordering': ['-date_joined'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('nationality', models.CharField(blank=True, max_length=100)),
                ('passport_number', models.CharField(blank=True, max_length=50)),
                ('passport_expiry', models.DateField(blank=True, null=True)),
                ('preferred_currency', models.CharField(choices=[('USD', 'US Dollar'), ('EUR', 'Euro'), ('GBP', 'British Pound'), ('CAD', 'Canadian Dollar'), ('AUD', 'Australian Dollar'), ('JPY', 'Japanese Yen'), ('CNY', 'Chinese Yuan'), ('INR', 'Indian Rupee')], default='USD', max_length=3)),
                ('preferred_language', models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('de', 'German'), ('it', 'Italian'), ('pt', 'Portuguese'), ('zh', 'Chinese'), ('ja', 'Japanese')], default='en', max_length=2)),
                ('preferred_travel_class', models.CharField(choices=[('economy', 'Economy'), ('premium_economy', 'Premium Economy'), ('business', 'Business'), ('first', 'First Class')], default='economy', max_length=20)),
                ('preferred_airlines', models.JSONField(blank=True, default=list)),
                ('preferred_hotel_chains', models.JSONField(blank=True, default=list)),
                ('frequent_flyer_programs', models.JSONField(blank=True, default=dict)),
                ('hotel_loyalty_programs', models.JSONField(blank=True, default=dict)),
                ('dietary_restrictions', models.JSONField(blank=True, default=list)),
                ('accessibility_needs', models.TextField(blank=True)),
                ('seat_preference', models.CharField(choices=[('window', 'Window'), ('aisle', 'Aisle'), ('any', 'Any')], default='any', max_length=20)),
                ('total_trips', models.IntegerField(default=0)),
                ('total_flights', models.IntegerField(default=0)),
                ('total_hotel_nights', models.IntegerField(default=0)),
                ('countries_visited', models.JSONField(blank=True, default=list)),
                ('cities_visited', models.JSONField(blank=True, default=list)),
                ('email_notifications', models.BooleanField(default=True)),
                ('sms_notifications', models.BooleanField(default=False)),
                ('push_notifications', models.BooleanField(default=True)),
                ('avatar', models.URLField(blank=True)),
                ('bio', models.TextField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='users.user')),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
                'db_table': 'user_profiles',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TravelHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_city', models.CharField(max_length=200)),
                ('destination_country', models.CharField(max_length=100)),
                ('origin_city', models.CharField(max_length=200)),
                ('origin_country', models.CharField(max_length=100)),
                ('departure_date', models.DateField()),
                ('return_date', models.DateField(blank=True, null=True)),
                ('trip_type', models.CharField(choices=[('business', 'Business'), ('leisure', 'Leisure'), ('both', 'Both')], default='leisure', max_length=20)),
                ('number_of_travelers', models.IntegerField(default=1)),
                ('booking_reference', models.CharField(blank=True, max_length=50)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='travel_history', to='users.user')),
            ],
            options={
                'verbose_name': 'Travel History',
                'verbose_name_plural': 'Travel Histories',
                'db_table': 'travel_history',
                'ordering': ['-departure_date'],
            },
        ),
        migrations.AddIndex(
            model_name='travelhistory',
            index=models.Index(fields=['user', '-departure_date'], name='travel_hist_user_id_b68d93_idx'),
        ),
        migrations.AddIndex(
            model_name='travelhistory',
            index=models.Index(fields=['destination_country'], name='travel_hist_destina_c6b8a2_idx'),
        ),
    ]
