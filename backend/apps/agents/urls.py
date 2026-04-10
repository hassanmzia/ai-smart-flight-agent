from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentSessionViewSet,
    AgentExecutionViewSet,
    AgentLogViewSet,
    RAGDocumentViewSet,
    plan_travel,
    chat,
    text_to_speech,
    auto_build_itinerary,
    # Multi-Modal
    voice_to_trip,
    image_to_trip,
    analyze_screenshot,
    # Autonomous Booking
    autonomous_book,
    confirm_autonomous_booking,
    # Debate
    debate_options,
    # Predictive Intelligence
    predict_prices,
    best_time_to_visit,
    destination_trends,
    crowd_levels,
    # Personalization
    get_travel_dna,
    get_recommendations,
    user_preferences,
    # Subscription
    subscription_status,
    check_feature_access,
    create_subscription,
    stripe_webhook,
    # Affiliate
    generate_affiliate_link,
    affiliate_report,
    affiliate_partners,
    affiliate_redirect,
    affiliate_admin_dashboard,
    # Price Watch
    create_price_watch,
    list_price_watches,
    # Collaborative
    collaboration_cost_split,
    # Real-Time Awareness
    live_context,
    crowd_levels_detail,
    # Language Tools
    translate_text,
    common_phrases,
    # Memory & Learning
    record_trip_memory,
    trip_memories,
    travel_insights,
    proactive_suggestions,
    feedback_summary,
    # Autonomous Agent v2
    flight_status_check,
    flight_rebooking,
    weather_adapt,
    disruption_impact,
    # Specialized Agents
    budget_tracker,
    budget_optimizer,
    etiquette_guide,
    local_customs,
    trip_health_check,
    pacing_plan,
)

app_name = 'agents'

router = DefaultRouter()
router.register(r'sessions', AgentSessionViewSet, basename='session')
router.register(r'executions', AgentExecutionViewSet, basename='execution')
router.register(r'logs', AgentLogViewSet, basename='log')
router.register(r'documents', RAGDocumentViewSet, basename='rag-document')

urlpatterns = [
    path('', include(router.urls)),
    path('plan', plan_travel, name='plan_travel'),
    path('chat', chat, name='chat'),
    path('tts', text_to_speech, name='text_to_speech'),
    path('auto-build', auto_build_itinerary, name='auto_build_itinerary'),
    # Multi-Modal Agent
    path('voice-to-trip', voice_to_trip, name='voice_to_trip'),
    path('image-to-trip', image_to_trip, name='image_to_trip'),
    path('analyze-screenshot', analyze_screenshot, name='analyze_screenshot'),
    # Autonomous Booking
    path('autonomous-book', autonomous_book, name='autonomous_book'),
    path('confirm-booking', confirm_autonomous_booking, name='confirm_autonomous_booking'),
    # Multi-Agent Debate
    path('debate', debate_options, name='debate_options'),
    # Predictive Intelligence
    path('predict-prices', predict_prices, name='predict_prices'),
    path('best-time', best_time_to_visit, name='best_time_to_visit'),
    path('trends', destination_trends, name='destination_trends'),
    path('crowd-levels', crowd_levels, name='crowd_levels'),
    # Personalization
    path('travel-dna', get_travel_dna, name='get_travel_dna'),
    path('recommendations', get_recommendations, name='get_recommendations'),
    path('preferences/me/', user_preferences, name='user_preferences'),
    # Subscription
    path('subscription', subscription_status, name='subscription_status'),
    path('subscription/create', create_subscription, name='create_subscription'),
    path('check-feature', check_feature_access, name='check_feature_access'),
    path('stripe-webhook', stripe_webhook, name='stripe_webhook'),
    # Affiliate
    path('affiliate/link', generate_affiliate_link, name='generate_affiliate_link'),
    path('affiliate/report', affiliate_report, name='affiliate_report'),
    path('affiliate/partners', affiliate_partners, name='affiliate_partners'),
    path('affiliate/redirect/<str:tracking_id>', affiliate_redirect, name='affiliate_redirect'),
    path('affiliate/admin-dashboard', affiliate_admin_dashboard, name='affiliate_admin_dashboard'),
    # Price Watch
    path('price-watch/create', create_price_watch, name='create_price_watch'),
    path('price-watch/list', list_price_watches, name='list_price_watches'),
    # Collaborative
    path('collaboration/<int:collaboration_id>/cost-split', collaboration_cost_split, name='collaboration_cost_split'),
    # Real-Time Awareness
    path('live-context', live_context, name='live_context'),
    path('crowd-levels-detail', crowd_levels_detail, name='crowd_levels_detail'),
    # Language Tools
    path('translate', translate_text, name='translate_text'),
    path('common-phrases', common_phrases, name='common_phrases'),
    # Memory & Learning
    path('memories', trip_memories, name='trip_memories'),
    path('memories/record', record_trip_memory, name='record_trip_memory'),
    path('memories/insights', travel_insights, name='travel_insights'),
    path('memories/suggestions', proactive_suggestions, name='proactive_suggestions'),
    path('memories/summary', feedback_summary, name='feedback_summary'),
    # Autonomous Agent v2
    path('flight-status', flight_status_check, name='flight_status_check'),
    path('flight-rebook', flight_rebooking, name='flight_rebooking'),
    path('weather-adapt', weather_adapt, name='weather_adapt'),
    path('disruption-impact', disruption_impact, name='disruption_impact'),
    # Specialized Agents
    path('budget/track', budget_tracker, name='budget_tracker'),
    path('budget/optimize', budget_optimizer, name='budget_optimizer'),
    path('etiquette', etiquette_guide, name='etiquette_guide'),
    path('local-customs', local_customs, name='local_customs'),
    path('health-check', trip_health_check, name='trip_health_check'),
    path('pacing-plan', pacing_plan, name='pacing_plan'),
]
