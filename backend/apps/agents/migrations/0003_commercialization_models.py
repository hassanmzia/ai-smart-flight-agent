"""
Migration for commercialization upgrade models:
AgentConversation, AgentMessage, AgentTask, UserPreference,
AgentAnalytics, AIModel, TripCollaboration, TripCollaborator,
CollaborationVote, Subscription, AffiliateClick, PriceWatch
"""
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('agents', '0002_add_rag_document_model'),
        ('itineraries', '0001_initial'),
    ]

    operations = [
        # AgentConversation
        migrations.CreateModel(
            name='AgentConversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('active', 'Active'), ('archived', 'Archived'), ('deleted', 'Deleted')], default='active', max_length=20)),
                ('is_archived', models.BooleanField(default=False)),
                ('conversation_type', models.CharField(choices=[('trip_planning', 'Trip Planning'), ('general', 'General'), ('booking_assist', 'Booking Assistance'), ('price_monitor', 'Price Monitor')], default='trip_planning', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_conversations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agent Conversation',
                'verbose_name_plural': 'Agent Conversations',
                'db_table': 'agent_conversations',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['user', '-updated_at'], name='agent_conve_user_id_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['status'], name='agent_conve_status_idx'),
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['conversation_type'], name='agent_conve_conv_type_idx'),
        ),
        migrations.AddIndex(
            model_name='agentconversation',
            index=models.Index(fields=['is_archived'], name='agent_conve_archived_idx'),
        ),

        # AgentMessage
        migrations.CreateModel(
            name='AgentMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('sender_type', models.CharField(choices=[('user', 'User'), ('agent', 'Agent'), ('system', 'System')], max_length=10)),
                ('message_type', models.CharField(choices=[('text', 'Text'), ('suggestion', 'Suggestion'), ('action', 'Action'), ('flight_result', 'Flight Result'), ('hotel_result', 'Hotel Result'), ('itinerary', 'Itinerary'), ('price_alert', 'Price Alert')], default='text', max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('intent', models.CharField(blank=True, max_length=100)),
                ('response_time_ms', models.IntegerField(blank=True, null=True)),
                ('tokens_used', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='agents.agentconversation')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='agent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agent Message',
                'verbose_name_plural': 'Agent Messages',
                'db_table': 'agent_messages',
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['conversation', 'created_at'], name='agent_msg_conv_created_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['sender_type'], name='agent_msg_sender_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['message_type'], name='agent_msg_type_idx'),
        ),
        migrations.AddIndex(
            model_name='agentmessage',
            index=models.Index(fields=['intent'], name='agent_msg_intent_idx'),
        ),

        # AgentTask
        migrations.CreateModel(
            name='AgentTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_type', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('parameters', models.JSONField(blank=True, default=dict)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_tasks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Agent Task',
                'verbose_name_plural': 'Agent Tasks',
                'db_table': 'agent_tasks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='agenttask',
            index=models.Index(fields=['user', '-created_at'], name='agent_task_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='agenttask',
            index=models.Index(fields=['status'], name='agent_task_status_idx'),
        ),
        migrations.AddIndex(
            model_name='agenttask',
            index=models.Index(fields=['task_type', 'status'], name='agent_task_type_status_idx'),
        ),

        # UserPreference
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preferences', models.JSONField(blank=True, default=dict)),
                ('travel_dna', models.JSONField(blank=True, default=dict)),
                ('preferred_airlines', models.JSONField(blank=True, default=list)),
                ('preferred_hotel_chains', models.JSONField(blank=True, default=list)),
                ('preferred_cuisines', models.JSONField(blank=True, default=list)),
                ('budget_range', models.CharField(choices=[('budget', 'Budget'), ('moderate', 'Moderate'), ('luxury', 'Luxury'), ('any', 'Any')], default='any', max_length=20)),
                ('trip_style', models.CharField(choices=[('adventure', 'Adventure'), ('relaxation', 'Relaxation'), ('cultural', 'Cultural'), ('business', 'Business'), ('family', 'Family')], default='cultural', max_length=20)),
                ('booking_advance_days', models.IntegerField(default=14, validators=[django.core.validators.MinValueValidator(0)])),
                ('last_trained', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Preference',
                'verbose_name_plural': 'User Preferences',
                'db_table': 'user_preferences',
            },
        ),

        # AgentAnalytics
        migrations.CreateModel(
            name='AgentAnalytics',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('metrics', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Agent Analytics',
                'verbose_name_plural': 'Agent Analytics',
                'db_table': 'agent_analytics',
                'ordering': ['-date'],
            },
        ),

        # AIModel
        migrations.CreateModel(
            name='AIModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('version', models.CharField(max_length=50)),
                ('model_type', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('config', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'AI Model',
                'verbose_name_plural': 'AI Models',
                'db_table': 'ai_models',
                'ordering': ['-created_at'],
            },
        ),

        # TripCollaboration
        migrations.CreateModel(
            name='TripCollaboration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Active'), ('closed', 'Closed')], default='active', max_length=10)),
                ('invite_code', models.CharField(max_length=20, unique=True)),
                ('max_participants', models.IntegerField(default=10, validators=[django.core.validators.MinValueValidator(1)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('itinerary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaborations', to='itineraries.itinerary')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_collaborations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Trip Collaboration',
                'verbose_name_plural': 'Trip Collaborations',
                'db_table': 'trip_collaborations',
                'ordering': ['-created_at'],
            },
        ),

        # TripCollaborator
        migrations.CreateModel(
            name='TripCollaborator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('viewer', 'Viewer'), ('editor', 'Editor'), ('admin', 'Admin')], default='editor', max_length=10)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('collaboration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaborators', to='agents.tripcollaboration')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trip_collaborations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Trip Collaborator',
                'verbose_name_plural': 'Trip Collaborators',
                'db_table': 'trip_collaborators',
                'ordering': ['-joined_at'],
                'unique_together': {('collaboration', 'user')},
            },
        ),

        # CollaborationVote
        migrations.CreateModel(
            name='CollaborationVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(choices=[('flight', 'Flight'), ('hotel', 'Hotel'), ('restaurant', 'Restaurant'), ('attraction', 'Attraction')], max_length=20)),
                ('item_id', models.CharField(max_length=255)),
                ('vote', models.CharField(choices=[('up', 'Up'), ('down', 'Down'), ('neutral', 'Neutral')], default='neutral', max_length=10)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('collaboration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='agents.tripcollaboration')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='collaboration_votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Collaboration Vote',
                'verbose_name_plural': 'Collaboration Votes',
                'db_table': 'collaboration_votes',
                'ordering': ['-created_at'],
            },
        ),

        # Subscription
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(choices=[('free', 'Free'), ('pro', 'Pro'), ('business', 'Business')], default='free', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('past_due', 'Past Due'), ('trialing', 'Trialing')], default='active', max_length=20)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=255)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=255)),
                ('current_period_start', models.DateTimeField(blank=True, null=True)),
                ('current_period_end', models.DateTimeField(blank=True, null=True)),
                ('ai_plans_used', models.IntegerField(default=0)),
                ('ai_plans_limit', models.IntegerField(default=3)),
                ('price_alerts_used', models.IntegerField(default=0)),
                ('price_alerts_limit', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'db_table': 'subscriptions',
            },
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['plan'], name='sub_plan_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['status'], name='sub_status_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['stripe_customer_id'], name='sub_stripe_cust_idx'),
        ),

        # AffiliateClick
        migrations.CreateModel(
            name='AffiliateClick',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('partner', models.CharField(max_length=100)),
                ('click_type', models.CharField(choices=[('flight', 'Flight'), ('hotel', 'Hotel'), ('car', 'Car'), ('activity', 'Activity')], max_length=20)),
                ('destination', models.CharField(blank=True, max_length=255)),
                ('tracking_id', models.CharField(max_length=255, unique=True)),
                ('revenue', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('clicked', 'Clicked'), ('converted', 'Converted'), ('paid', 'Paid')], default='clicked', max_length=20)),
                ('clicked_at', models.DateTimeField(auto_now_add=True)),
                ('converted_at', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='affiliate_clicks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Affiliate Click',
                'verbose_name_plural': 'Affiliate Clicks',
                'db_table': 'affiliate_clicks',
                'ordering': ['-clicked_at'],
            },
        ),
        migrations.AddIndex(
            model_name='affiliateclick',
            index=models.Index(fields=['partner', '-clicked_at'], name='aff_partner_clicked_idx'),
        ),
        migrations.AddIndex(
            model_name='affiliateclick',
            index=models.Index(fields=['tracking_id'], name='aff_tracking_idx'),
        ),
        migrations.AddIndex(
            model_name='affiliateclick',
            index=models.Index(fields=['status'], name='aff_status_idx'),
        ),

        # PriceWatch
        migrations.CreateModel(
            name='PriceWatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('watch_type', models.CharField(choices=[('flight', 'Flight'), ('hotel', 'Hotel')], max_length=10)),
                ('search_params', models.JSONField()),
                ('target_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('current_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('lowest_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('price_history', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('last_checked', models.DateTimeField(blank=True, null=True)),
                ('notify_on_any_drop', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='price_watches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Price Watch',
                'verbose_name_plural': 'Price Watches',
                'db_table': 'price_watches',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='pricewatch',
            index=models.Index(fields=['user', '-created_at'], name='pw_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='pricewatch',
            index=models.Index(fields=['is_active'], name='pw_active_idx'),
        ),
        migrations.AddIndex(
            model_name='pricewatch',
            index=models.Index(fields=['is_active', 'last_checked'], name='pw_active_checked_idx'),
        ),
    ]
