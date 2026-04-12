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
    trip_experience_preview,
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
    voice_to_voice_translate,
    offline_phrase_pack,
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
    # Phase 5: Monetization & Partnerships
    register_partner,
    create_coupon,
    list_coupons,
    redeem_coupon,
    my_referral,
    send_referral,
    partner_dashboard,
    calculate_savings,
    # Destination Knowledge Base
    destination_knowledge,
    destination_cultural_info,
    submit_destination_tip,
    vote_destination_tip,
    search_destinations_kb,
    destination_festivals,
    destination_etiquette,
    # Phase 6: Social & Viral Growth
    generate_story,
    generate_social_cards,
    get_story,
    my_stories,
    public_stories,
    toggle_story_like,
    add_story_comment,
    publish_story,
    # Trip Templates
    create_trip_template,
    generate_trip_template,
    browse_templates,
    get_template_detail,
    clone_template,
    like_template,
    rate_template,
    featured_templates,
    my_templates,
    # Content Hub
    submit_content,
    destination_content,
    vote_content,
    trending_content,
    my_content,
    destination_content_stats,
    # Collaborative Filtering
    similar_users,
    people_like_you,
    social_proof,
    enjoyment_prediction,
    # Phase 7: Faith & Health Awareness
    prayer_times,
    worship_places,
    spiritual_sites,
    dietary_restaurants,
    ramadan_schedule,
    faith_travel_summary,
    medical_facilities,
    accessibility_info,
    submit_accessibility_rating,
    medication_reminders,
    medication_timezone_adjust,
    health_insurance_info,
    fatigue_itinerary,
    health_travel_summary,
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
    path('trip-experience', trip_experience_preview, name='trip_experience_preview'),
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
    path('voice-translate', voice_to_voice_translate, name='voice_to_voice_translate'),
    path('offline-phrases', offline_phrase_pack, name='offline_phrase_pack'),
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
    # Phase 5: Partnerships & Coupons
    path('partners/register', register_partner, name='register_partner'),
    path('partners/dashboard', partner_dashboard, name='partner_dashboard'),
    path('coupons', list_coupons, name='list_coupons'),
    path('coupons/create', create_coupon, name='create_coupon'),
    path('coupons/redeem', redeem_coupon, name='redeem_coupon'),
    path('referral', my_referral, name='my_referral'),
    path('referral/send', send_referral, name='send_referral'),
    path('savings/calculate', calculate_savings, name='calculate_savings'),
    # Destination Knowledge Base
    path('destinations/knowledge', destination_knowledge, name='destination_knowledge'),
    path('destinations/cultural-info', destination_cultural_info, name='destination_cultural_info'),
    path('destinations/tips/submit', submit_destination_tip, name='submit_destination_tip'),
    path('destinations/tips/vote', vote_destination_tip, name='vote_destination_tip'),
    path('destinations/search', search_destinations_kb, name='search_destinations_kb'),
    path('destinations/festivals', destination_festivals, name='destination_festivals'),
    path('destinations/etiquette', destination_etiquette, name='destination_etiquette'),
    # Phase 6: Stories
    path('stories/generate', generate_story, name='generate_story'),
    path('stories/social-cards', generate_social_cards, name='generate_social_cards'),
    path('stories/mine', my_stories, name='my_stories'),
    path('stories/public', public_stories, name='public_stories'),
    path('stories/like', toggle_story_like, name='toggle_story_like'),
    path('stories/comment', add_story_comment, name='add_story_comment'),
    path('stories/publish', publish_story, name='publish_story'),
    path('stories/<str:share_token>', get_story, name='get_story'),
    # Phase 6: Trip Templates
    path('templates/create', create_trip_template, name='create_trip_template'),
    path('templates/generate', generate_trip_template, name='generate_trip_template'),
    path('templates/browse', browse_templates, name='browse_templates'),
    path('templates/featured', featured_templates, name='featured_templates'),
    path('templates/mine', my_templates, name='my_templates'),
    path('templates/clone', clone_template, name='clone_template'),
    path('templates/like', like_template, name='like_template'),
    path('templates/rate', rate_template, name='rate_template'),
    path('templates/<int:template_id>', get_template_detail, name='get_template_detail'),
    # Phase 6: Content Hub
    path('content/submit', submit_content, name='submit_content'),
    path('content/destination', destination_content, name='destination_content'),
    path('content/vote', vote_content, name='vote_content'),
    path('content/trending', trending_content, name='trending_content'),
    path('content/mine', my_content, name='my_content'),
    path('content/stats', destination_content_stats, name='destination_content_stats'),
    # Collaborative Filtering
    path('community/similar-users', similar_users, name='similar_users'),
    path('community/people-like-you', people_like_you, name='people_like_you'),
    path('community/social-proof', social_proof, name='social_proof'),
    path('community/enjoyment-prediction', enjoyment_prediction, name='enjoyment_prediction'),
    # Phase 7: Faith Travel
    path('faith/prayer-times', prayer_times, name='prayer_times'),
    path('faith/worship-places', worship_places, name='worship_places'),
    path('faith/spiritual-sites', spiritual_sites, name='spiritual_sites'),
    path('faith/dietary-restaurants', dietary_restaurants, name='dietary_restaurants'),
    path('faith/ramadan-schedule', ramadan_schedule, name='ramadan_schedule'),
    path('faith/summary', faith_travel_summary, name='faith_travel_summary'),
    # Phase 7: Health Travel
    path('health/medical-facilities', medical_facilities, name='medical_facilities'),
    path('health/accessibility', accessibility_info, name='accessibility_info'),
    path('health/accessibility/rate', submit_accessibility_rating, name='submit_accessibility_rating'),
    path('health/medication-reminders', medication_reminders, name='medication_reminders'),
    path('health/medication-adjust', medication_timezone_adjust, name='medication_timezone_adjust'),
    path('health/insurance', health_insurance_info, name='health_insurance_info'),
    path('health/fatigue-itinerary', fatigue_itinerary, name='fatigue_itinerary'),
    path('health/summary', health_travel_summary, name='health_travel_summary'),
]
