"""
Subscription Middleware
Enforces freemium plan limits on AI features.
Tracks usage and blocks requests when limits are exceeded.
"""
import logging
from functools import wraps
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Plan limits configuration
PLAN_LIMITS = {
    'free': {
        'ai_plans_limit': 3,
        'price_alerts_limit': 1,
        'collaborators_limit': 2,
        'voice_enabled': False,
        'auto_builder_enabled': False,
        'autonomous_agent': False,
        '3d_visualization': False,
        'translations_limit': 5,
        'destination_kb': True,
        'coupons_enabled': True,
        'referrals_enabled': True,
        'api_access': False,
        'ai_concierge': False,
        'priority_booking': False,
        'ads_shown': True,
    },
    'pro': {
        'ai_plans_limit': 999999,  # Unlimited
        'price_alerts_limit': 10,
        'collaborators_limit': 10,
        'voice_enabled': True,
        'auto_builder_enabled': True,
        'autonomous_agent': True,
        '3d_visualization': True,
        'translations_limit': 999999,
        'destination_kb': True,
        'coupons_enabled': True,
        'referrals_enabled': True,
        'api_access': False,
        'ai_concierge': False,
        'priority_booking': False,
        'ads_shown': False,
    },
    'business': {
        'ai_plans_limit': 999999,
        'price_alerts_limit': 999999,
        'collaborators_limit': 999999,
        'voice_enabled': True,
        'auto_builder_enabled': True,
        'autonomous_agent': True,
        '3d_visualization': True,
        'translations_limit': 999999,
        'destination_kb': True,
        'coupons_enabled': True,
        'referrals_enabled': True,
        'api_access': True,
        'ai_concierge': True,
        'priority_booking': True,
        'ads_shown': False,
    },
}


def get_user_subscription(user):
    """Get or create a subscription for the user."""
    from apps.agents.models import Subscription
    sub, created = Subscription.objects.get_or_create(
        user=user,
        defaults={'plan': 'free', 'status': 'active'}
    )

    # Reset monthly counters if period expired
    if sub.current_period_end and timezone.now() > sub.current_period_end:
        sub.ai_plans_used = 0
        sub.price_alerts_used = 0
        sub.current_period_start = timezone.now()
        sub.current_period_end = timezone.now() + timedelta(days=30)
        sub.save()

    return sub


def get_plan_limits(plan: str) -> dict:
    """Get limits for a subscription plan."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])


def check_usage(user, feature: str) -> dict:
    """
    Check if user can use a feature based on their subscription.
    Returns dict with 'allowed' boolean and details.
    """
    sub = get_user_subscription(user)
    limits = get_plan_limits(sub.plan)

    if feature == 'ai_plan':
        used = sub.ai_plans_used
        limit = limits['ai_plans_limit']
        allowed = used < limit
        return {
            'allowed': allowed,
            'used': used,
            'limit': limit,
            'feature': 'AI Trip Plans',
            'plan': sub.plan,
            'upgrade_message': f'You have used {used}/{limit} AI plans this month. Upgrade to Pro for unlimited.' if not allowed else None,
        }

    elif feature == 'price_alert':
        used = sub.price_alerts_used
        limit = limits['price_alerts_limit']
        allowed = used < limit
        return {
            'allowed': allowed,
            'used': used,
            'limit': limit,
            'feature': 'Price Alerts',
            'plan': sub.plan,
            'upgrade_message': f'You have {used}/{limit} active price alerts. Upgrade to Pro for more.' if not allowed else None,
        }

    elif feature == 'voice':
        allowed = limits['voice_enabled']
        return {
            'allowed': allowed,
            'feature': 'Voice Planning',
            'plan': sub.plan,
            'upgrade_message': 'Voice planning is available on Pro and Business plans.' if not allowed else None,
        }

    elif feature == 'auto_builder':
        allowed = limits['auto_builder_enabled']
        return {
            'allowed': allowed,
            'feature': 'Smart Auto-Builder',
            'plan': sub.plan,
            'upgrade_message': 'Auto-builder is available on Pro and Business plans.' if not allowed else None,
        }

    elif feature == 'collaborators':
        limit = limits['collaborators_limit']
        return {
            'allowed': True,  # Always allowed, limit checked at invite time
            'limit': limit,
            'feature': 'Trip Collaborators',
            'plan': sub.plan,
        }

    elif feature == 'autonomous_agent':
        allowed = limits.get('autonomous_agent', False)
        return {
            'allowed': allowed,
            'feature': 'Autonomous Booking Agent',
            'plan': sub.plan,
            'upgrade_message': 'Autonomous agent is available on Pro and Business plans.' if not allowed else None,
        }

    elif feature == '3d_visualization':
        allowed = limits.get('3d_visualization', False)
        return {
            'allowed': allowed,
            'feature': '3D Trip Visualization',
            'plan': sub.plan,
            'upgrade_message': '3D visualization is available on Pro and Business plans.' if not allowed else None,
        }

    elif feature == 'translations':
        used = getattr(sub, 'translations_used', 0)
        limit = limits.get('translations_limit', 5)
        allowed = used < limit
        return {
            'allowed': allowed,
            'used': used,
            'limit': limit,
            'feature': 'AI Translations',
            'plan': sub.plan,
            'upgrade_message': f'You have used {used}/{limit} translations this month. Upgrade to Pro for unlimited.' if not allowed else None,
        }

    elif feature == 'api_access':
        allowed = limits.get('api_access', False)
        return {
            'allowed': allowed,
            'feature': 'API Access',
            'plan': sub.plan,
            'upgrade_message': 'API access is available on the Business plan.' if not allowed else None,
        }

    elif feature == 'ai_concierge':
        allowed = limits.get('ai_concierge', False)
        return {
            'allowed': allowed,
            'feature': 'AI Concierge',
            'plan': sub.plan,
            'upgrade_message': 'AI Concierge is available on the Business plan.' if not allowed else None,
        }

    elif feature == 'priority_booking':
        allowed = limits.get('priority_booking', False)
        return {
            'allowed': allowed,
            'feature': 'Priority Booking',
            'plan': sub.plan,
            'upgrade_message': 'Priority booking is available on the Business plan.' if not allowed else None,
        }

    return {'allowed': True, 'plan': sub.plan}


def increment_usage(user, feature: str):
    """Increment usage counter for a feature."""
    sub = get_user_subscription(user)

    if feature == 'ai_plan':
        sub.ai_plans_used += 1
        sub.save(update_fields=['ai_plans_used'])
    elif feature == 'price_alert':
        sub.price_alerts_used += 1
        sub.save(update_fields=['price_alerts_used'])


def require_subscription(feature: str):
    """
    Decorator for DRF views that checks subscription limits.
    Usage: @require_subscription('ai_plan')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)

            usage = check_usage(request.user, feature)
            if not usage['allowed']:
                return JsonResponse({
                    'error': 'subscription_limit_exceeded',
                    'message': usage.get('upgrade_message', 'Plan limit reached'),
                    'feature': usage['feature'],
                    'plan': usage['plan'],
                    'used': usage.get('used'),
                    'limit': usage.get('limit'),
                }, status=403)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def get_subscription_status(user) -> dict:
    """Get full subscription status for a user."""
    sub = get_user_subscription(user)
    limits = get_plan_limits(sub.plan)

    return {
        'plan': sub.plan,
        'status': sub.status,
        'usage': {
            'ai_plans': {'used': sub.ai_plans_used, 'limit': limits['ai_plans_limit']},
            'price_alerts': {'used': sub.price_alerts_used, 'limit': limits['price_alerts_limit']},
        },
        'features': {
            'voice_enabled': limits['voice_enabled'],
            'auto_builder_enabled': limits['auto_builder_enabled'],
            'collaborators_limit': limits['collaborators_limit'],
            'autonomous_agent': limits.get('autonomous_agent', False),
            '3d_visualization': limits.get('3d_visualization', False),
            'translations_limit': limits.get('translations_limit', 5),
            'api_access': limits.get('api_access', False),
            'ai_concierge': limits.get('ai_concierge', False),
            'priority_booking': limits.get('priority_booking', False),
            'ads_shown': limits.get('ads_shown', True),
        },
        'period': {
            'start': sub.current_period_start.isoformat() if sub.current_period_start else None,
            'end': sub.current_period_end.isoformat() if sub.current_period_end else None,
        },
        'stripe_customer_id': sub.stripe_customer_id or None,
    }
