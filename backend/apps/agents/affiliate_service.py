"""
Affiliate Revenue Service
Tracks clicks, conversions, and revenue from partner referrals.
Generates tracking links for flights, hotels, and activities.
"""
import uuid
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

# Partner configuration
AFFILIATE_PARTNERS = {
    'booking_com': {
        'name': 'Booking.com',
        'base_url': 'https://www.booking.com',
        'commission_rate': 0.04,  # 4%
        'types': ['hotel'],
    },
    'skyscanner': {
        'name': 'Skyscanner',
        'base_url': 'https://www.skyscanner.com',
        'commission_rate': 0.02,  # 2%
        'types': ['flight'],
    },
    'expedia': {
        'name': 'Expedia',
        'base_url': 'https://www.expedia.com',
        'commission_rate': 0.03,  # 3%
        'types': ['flight', 'hotel', 'car', 'activity'],
    },
    'getyourguide': {
        'name': 'GetYourGuide',
        'base_url': 'https://www.getyourguide.com',
        'commission_rate': 0.08,  # 8%
        'types': ['activity'],
    },
    'rentalcars': {
        'name': 'Rentalcars.com',
        'base_url': 'https://www.rentalcars.com',
        'commission_rate': 0.05,  # 5%
        'types': ['car'],
    },
}


class AffiliateService:
    """Manages affiliate link generation, click tracking, and revenue."""

    @staticmethod
    def generate_tracking_link(partner: str, click_type: str,
                                destination: str = '', user=None,
                                metadata: dict = None) -> Dict[str, Any]:
        """
        Generate a tracked affiliate link.
        Returns the tracking ID and destination URL.
        """
        from .models import AffiliateClick

        partner_config = AFFILIATE_PARTNERS.get(partner)
        if not partner_config:
            return {'success': False, 'error': f'Unknown partner: {partner}'}

        if click_type not in partner_config['types']:
            return {'success': False, 'error': f'{partner} does not support {click_type}'}

        tracking_id = f"aff-{uuid.uuid4().hex[:12]}"

        click = AffiliateClick.objects.create(
            user=user,
            partner=partner,
            click_type=click_type,
            destination=destination,
            tracking_id=tracking_id,
            status='clicked',
        )

        # Build affiliate URL with tracking
        base_url = partner_config['base_url']
        affiliate_url = f"{base_url}?aid={tracking_id}&dest={destination}"

        return {
            'success': True,
            'tracking_id': tracking_id,
            'affiliate_url': affiliate_url,
            'partner': partner_config['name'],
            'click_id': click.id,
        }

    @staticmethod
    def record_conversion(tracking_id: str, revenue: float = 0) -> Dict[str, Any]:
        """Record a conversion (user completed a booking via affiliate link)."""
        from .models import AffiliateClick

        try:
            click = AffiliateClick.objects.get(tracking_id=tracking_id)

            partner_config = AFFILIATE_PARTNERS.get(click.partner, {})
            commission_rate = partner_config.get('commission_rate', 0.03)

            click.status = 'converted'
            click.converted_at = timezone.now()
            click.revenue = Decimal(str(revenue * commission_rate))
            click.save()

            return {
                'success': True,
                'tracking_id': tracking_id,
                'revenue': float(click.revenue),
                'commission_rate': commission_rate,
            }
        except AffiliateClick.DoesNotExist:
            return {'success': False, 'error': 'Tracking ID not found'}

    @staticmethod
    def get_revenue_report(user=None, days: int = 30) -> Dict[str, Any]:
        """Generate affiliate revenue report."""
        from .models import AffiliateClick
        from django.db.models import Sum, Count

        cutoff = timezone.now() - timezone.timedelta(days=days)
        qs = AffiliateClick.objects.filter(clicked_at__gte=cutoff)

        if user and not user.is_staff:
            qs = qs.filter(user=user)

        total_clicks = qs.count()
        conversions = qs.filter(status='converted')
        total_revenue = conversions.aggregate(total=Sum('revenue'))['total'] or 0

        by_partner = qs.values('partner').annotate(
            clicks=Count('id'),
            conversions_count=Count('id', filter=models_Q(status='converted')),
            revenue=Sum('revenue'),
        )

        return {
            'success': True,
            'period_days': days,
            'total_clicks': total_clicks,
            'total_conversions': conversions.count(),
            'conversion_rate': f"{(conversions.count() / total_clicks * 100):.1f}%" if total_clicks else "0%",
            'total_revenue': float(total_revenue),
            'by_partner': list(by_partner),
        }

    @staticmethod
    def get_available_partners(click_type: str = None) -> list:
        """Get list of available affiliate partners, optionally filtered by type."""
        partners = []
        for key, config in AFFILIATE_PARTNERS.items():
            if click_type and click_type not in config['types']:
                continue
            partners.append({
                'id': key,
                'name': config['name'],
                'types': config['types'],
                'commission_rate': f"{config['commission_rate'] * 100:.0f}%",
            })
        return partners


def models_Q(**kwargs):
    """Helper to import Q."""
    from django.db.models import Q
    return Q(**kwargs)
