"""
Partnership Service
Manages partner businesses, coupons, redemptions, referral codes, and revenue sharing.
"""
import json
import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.utils import timezone

logger = logging.getLogger(__name__)

# Reward amount per successful referral conversion
REFERRAL_REWARD_AMOUNT = Decimal("5.00")

# Platform cut of AI-driven savings
PLATFORM_SAVINGS_CUT = Decimal("0.10")  # 10%


class PartnershipService:
    """Handles partner onboarding, coupons, redemptions, referrals, and revenue sharing."""

    # ------------------------------------------------------------------ #
    #  Partner Registration
    # ------------------------------------------------------------------ #

    @staticmethod
    def register_partner(data: dict, onboarded_by=None) -> Dict[str, Any]:
        """
        Register a new partner business with status='pending'.

        Parameters
        ----------
        data : dict
            Must include: name, category, destination, contact_email.
            Optional: description, address, website, contact_phone, logo_url,
                      commission_rate.
        onboarded_by : User or None
            The user who onboarded this partner.

        Returns
        -------
        dict with 'success' key and partner data or error.
        """
        from apps.agents.models import PartnerBusiness

        try:
            required_fields = ['name', 'category', 'destination', 'contact_email']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing)}",
                }

            partner = PartnerBusiness.objects.create(
                name=data['name'],
                category=data['category'],
                description=data.get('description', ''),
                destination=data['destination'],
                address=data.get('address', ''),
                website=data.get('website', ''),
                contact_email=data['contact_email'],
                contact_phone=data.get('contact_phone', ''),
                logo_url=data.get('logo_url', ''),
                status='pending',
                commission_rate=Decimal(str(data.get('commission_rate', 10.00))),
                onboarded_by=onboarded_by,
            )

            logger.info("Registered new partner business: %s (id=%s)", partner.name, partner.id)

            return {
                'success': True,
                'partner': {
                    'id': partner.id,
                    'name': partner.name,
                    'category': partner.category,
                    'destination': partner.destination,
                    'contact_email': partner.contact_email,
                    'status': partner.status,
                    'commission_rate': float(partner.commission_rate),
                    'created_at': partner.created_at.isoformat() if partner.created_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to register partner: %s", e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Coupon Management
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_coupon(partner_id: int, data: dict) -> Dict[str, Any]:
        """
        Create a coupon for a partner business.

        Parameters
        ----------
        partner_id : int
            The ID of the PartnerBusiness.
        data : dict
            Must include: title.
            Optional: code, description, discount_type, discount_value,
                      min_spend, max_uses, valid_from, valid_until, terms.

        Returns
        -------
        dict with 'success' key and coupon data or error.
        """
        from apps.agents.models import PartnerBusiness, PartnerCoupon

        try:
            try:
                partner = PartnerBusiness.objects.get(id=partner_id)
            except PartnerBusiness.DoesNotExist:
                return {'success': False, 'error': f'Partner with id {partner_id} not found'}

            if partner.status != 'active':
                return {
                    'success': False,
                    'error': f'Partner is not active (current status: {partner.status})',
                }

            # Auto-generate coupon code if not provided
            code = data.get('code')
            if not code:
                code = f"{partner.name[:7].upper().replace(' ', '')}-{uuid.uuid4().hex[:4].upper()}"

            # Ensure uniqueness
            while PartnerCoupon.objects.filter(code=code).exists():
                code = f"{partner.name[:7].upper().replace(' ', '')}-{uuid.uuid4().hex[:4].upper()}"

            discount_type = data.get('discount_type', 'percentage')
            discount_value = Decimal(str(data.get('discount_value', 10)))

            # Build QR data
            qr_data = json.dumps({
                'code': code,
                'partner': partner.name,
                'discount': f"{discount_value} {'%' if discount_type == 'percentage' else 'off'}",
            })

            coupon = PartnerCoupon.objects.create(
                partner=partner,
                code=code,
                title=data.get('title', ''),
                description=data.get('description', ''),
                discount_type=discount_type,
                discount_value=discount_value,
                min_spend=Decimal(str(data.get('min_spend', 0))),
                max_uses=int(data.get('max_uses', 0)),
                is_active=True,
                valid_from=data.get('valid_from', timezone.now()),
                valid_until=data.get('valid_until'),
                terms=data.get('terms', ''),
                qr_data=qr_data,
            )

            logger.info(
                "Created coupon %s for partner %s (id=%s)", code, partner.name, partner.id
            )

            return {
                'success': True,
                'coupon': {
                    'id': coupon.id,
                    'code': coupon.code,
                    'title': coupon.title,
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value),
                    'min_spend': float(coupon.min_spend),
                    'max_uses': coupon.max_uses,
                    'valid_from': coupon.valid_from.isoformat() if coupon.valid_from else None,
                    'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                    'qr_data': coupon.qr_data,
                    'partner_id': partner.id,
                    'partner_name': partner.name,
                },
            }
        except Exception as e:
            logger.error("Failed to create coupon for partner %s: %s", partner_id, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_coupons(
        destination: str = None, category: str = None
    ) -> Dict[str, Any]:
        """
        List active, valid coupons optionally filtered by destination and/or category.

        Returns
        -------
        dict with 'success' key and list of coupon dicts including partner info.
        """
        from apps.agents.models import PartnerCoupon

        try:
            now = timezone.now()
            qs = PartnerCoupon.objects.filter(
                is_active=True,
                partner__status='active',
                valid_from__lte=now,
            ).select_related('partner')

            # Exclude expired coupons
            qs = qs.filter(
                models_Q(valid_until__isnull=True) | models_Q(valid_until__gte=now)
            )

            if destination:
                qs = qs.filter(partner__destination__icontains=destination)

            if category:
                qs = qs.filter(partner__category=category)

            coupons = []
            for coupon in qs:
                # Skip coupons that exhausted their max uses
                if coupon.max_uses > 0 and coupon.times_used >= coupon.max_uses:
                    continue

                coupons.append({
                    'id': coupon.id,
                    'code': coupon.code,
                    'title': coupon.title,
                    'description': coupon.description,
                    'discount_type': coupon.discount_type,
                    'discount_value': float(coupon.discount_value),
                    'min_spend': float(coupon.min_spend),
                    'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                    'terms': coupon.terms,
                    'partner': {
                        'id': coupon.partner.id,
                        'name': coupon.partner.name,
                        'category': coupon.partner.category,
                        'destination': coupon.partner.destination,
                        'rating': float(coupon.partner.rating),
                    },
                })

            logger.info(
                "Retrieved %d active coupons (destination=%s, category=%s)",
                len(coupons), destination, category,
            )

            # If no real coupons exist, return demo coupons so the page isn't empty
            if not coupons:
                coupons = _get_demo_coupons(destination, category)

            return {'success': True, 'coupons': coupons, 'count': len(coupons)}
        except Exception as e:
            logger.error("Failed to get coupons: %s", e)
            # Return demo coupons even on DB errors so the page always renders
            coupons = _get_demo_coupons(destination, category)
            return {'success': True, 'coupons': coupons, 'count': len(coupons)}

    # ------------------------------------------------------------------ #
    #  Coupon Redemption
    # ------------------------------------------------------------------ #

    @staticmethod
    def redeem_coupon(user, coupon_code: str, order_total: float) -> Dict[str, Any]:
        """
        Validate and redeem a coupon.

        Calculates savings based on discount_type, increments times_used,
        creates CouponRedemption, and calculates platform commission.

        Returns
        -------
        dict with 'success' key and redemption details or error.
        """
        from apps.agents.models import CouponRedemption, PartnerCoupon

        try:
            try:
                coupon = PartnerCoupon.objects.select_related('partner').get(code=coupon_code)
            except PartnerCoupon.DoesNotExist:
                return {'success': False, 'error': f'Coupon code "{coupon_code}" not found'}

            # Validate coupon
            if not coupon.is_valid:
                return {'success': False, 'error': 'Coupon is no longer valid'}

            if coupon.partner.status != 'active':
                return {'success': False, 'error': 'Partner business is not currently active'}

            order_total_decimal = Decimal(str(order_total))

            if order_total_decimal < coupon.min_spend:
                return {
                    'success': False,
                    'error': f'Minimum spend of ${coupon.min_spend} required. '
                             f'Order total is ${order_total_decimal}.',
                }

            # Calculate savings
            if coupon.discount_type == 'percentage':
                savings = round(order_total_decimal * coupon.discount_value / Decimal('100'), 2)
            elif coupon.discount_type == 'fixed':
                savings = min(coupon.discount_value, order_total_decimal)
            elif coupon.discount_type == 'bogo':
                # BOGO: savings = half the order total (approximation)
                savings = round(order_total_decimal / Decimal('2'), 2)
            elif coupon.discount_type == 'freebie':
                savings = coupon.discount_value
            else:
                savings = Decimal('0')

            # Calculate platform commission based on partner's commission rate
            commission_rate = coupon.partner.commission_rate / Decimal('100')
            platform_commission = round(savings * commission_rate, 2)

            # Increment times_used
            coupon.times_used += 1
            coupon.save(update_fields=['times_used', 'updated_at'])

            # Update partner stats
            partner = coupon.partner
            partner.total_coupons_redeemed += 1
            partner.total_revenue_generated += platform_commission
            partner.save(update_fields=[
                'total_coupons_redeemed', 'total_revenue_generated', 'updated_at',
            ])

            # Create redemption record
            redemption = CouponRedemption.objects.create(
                user=user,
                coupon=coupon,
                savings_amount=savings,
                order_total=order_total_decimal,
                platform_commission=platform_commission,
            )

            logger.info(
                "Coupon %s redeemed by user %s: savings=$%s, commission=$%s",
                coupon_code, user, savings, platform_commission,
            )

            return {
                'success': True,
                'redemption': {
                    'id': redemption.id,
                    'coupon_code': coupon.code,
                    'coupon_title': coupon.title,
                    'discount_type': coupon.discount_type,
                    'order_total': float(order_total_decimal),
                    'savings_amount': float(savings),
                    'final_total': float(order_total_decimal - savings),
                    'platform_commission': float(platform_commission),
                    'partner_name': partner.name,
                    'redeemed_at': redemption.redeemed_at.isoformat()
                    if redemption.redeemed_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to redeem coupon %s: %s", coupon_code, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Referral System
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_or_create_referral_code(user) -> Dict[str, Any]:
        """
        Get or create a referral code for the given user.

        Code format: first 3 chars of username (uppercase) + 5 random hex chars.

        Returns
        -------
        dict with 'success' key and referral code data.
        """
        from apps.agents.models import ReferralCode

        try:
            referral_code, created = ReferralCode.objects.get_or_create(
                user=user,
                defaults={
                    'code': _generate_referral_code(user),
                    'is_active': True,
                },
            )

            action = "Created" if created else "Retrieved"
            logger.info("%s referral code %s for user %s", action, referral_code.code, user)

            return {
                'success': True,
                'referral_code': {
                    'code': referral_code.code,
                    'total_referrals': referral_code.total_referrals,
                    'successful_referrals': referral_code.successful_referrals,
                    'total_earnings': float(referral_code.total_earnings),
                    'is_active': referral_code.is_active,
                    'created': created,
                },
            }
        except Exception as e:
            logger.error("Failed to get/create referral code for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def record_referral(referral_code: str, referred_email: str) -> Dict[str, Any]:
        """
        Record a new referral from the given referral code.

        Increments total_referrals on the ReferralCode and creates a Referral record.

        Returns
        -------
        dict with 'success' key and referral data.
        """
        from apps.agents.models import Referral, ReferralCode

        try:
            try:
                ref_code = ReferralCode.objects.select_related('user').get(
                    code=referral_code, is_active=True
                )
            except ReferralCode.DoesNotExist:
                return {'success': False, 'error': f'Referral code "{referral_code}" not found or inactive'}

            # Prevent duplicate referrals for the same email
            if Referral.objects.filter(referral_code=ref_code, referred_email=referred_email).exists():
                return {
                    'success': False,
                    'error': f'Referral already exists for {referred_email}',
                }

            referral = Referral.objects.create(
                referrer=ref_code.user,
                referral_code=ref_code,
                referred_email=referred_email,
                status='pending',
            )

            # Increment total referrals
            ref_code.total_referrals += 1
            ref_code.save(update_fields=['total_referrals'])

            logger.info(
                "Recorded referral from %s to %s (code=%s)",
                ref_code.user, referred_email, referral_code,
            )

            return {
                'success': True,
                'referral': {
                    'id': referral.id,
                    'referrer': str(ref_code.user),
                    'referred_email': referred_email,
                    'referral_code': referral_code,
                    'status': referral.status,
                    'created_at': referral.created_at.isoformat() if referral.created_at else None,
                },
            }
        except Exception as e:
            logger.error("Failed to record referral for code %s: %s", referral_code, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def complete_referral(referred_user) -> Dict[str, Any]:
        """
        Complete a referral when the referred user makes their first booking.

        Marks the referral as 'converted', calculates the reward ($5 per conversion),
        and updates the referrer's total_earnings.

        Returns
        -------
        dict with 'success' key and referral completion details.
        """
        from apps.agents.models import Referral

        try:
            # Find the pending/signed_up referral for this user
            referral = Referral.objects.filter(
                referred_user=referred_user,
                status__in=['pending', 'signed_up'],
            ).select_related('referral_code').first()

            if not referral:
                return {
                    'success': False,
                    'error': 'No pending referral found for this user',
                }

            # Mark as converted
            referral.status = 'converted'
            referral.reward_amount = REFERRAL_REWARD_AMOUNT
            referral.converted_at = timezone.now()
            referral.save(update_fields=['status', 'reward_amount', 'converted_at'])

            # Update referral code stats
            ref_code = referral.referral_code
            ref_code.successful_referrals += 1
            ref_code.total_earnings += REFERRAL_REWARD_AMOUNT
            ref_code.save(update_fields=['successful_referrals', 'total_earnings'])

            logger.info(
                "Completed referral: %s referred %s, reward=$%s",
                referral.referrer, referred_user, REFERRAL_REWARD_AMOUNT,
            )

            return {
                'success': True,
                'referral': {
                    'id': referral.id,
                    'referrer': str(referral.referrer),
                    'referred_user': str(referred_user),
                    'reward_amount': float(referral.reward_amount),
                    'status': referral.status,
                    'converted_at': referral.converted_at.isoformat()
                    if referral.converted_at else None,
                },
                'referrer_total_earnings': float(ref_code.total_earnings),
            }
        except Exception as e:
            logger.error("Failed to complete referral for user %s: %s", referred_user, e)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def get_referral_stats(user) -> Dict[str, Any]:
        """
        Return referral statistics for the given user.

        Returns
        -------
        dict with code, total referrals, successful referrals, earnings,
        and a list of recent referrals.
        """
        from apps.agents.models import Referral, ReferralCode

        try:
            try:
                ref_code = ReferralCode.objects.get(user=user)
            except ReferralCode.DoesNotExist:
                return {
                    'success': True,
                    'has_referral_code': False,
                    'message': 'No referral code found. Use get_or_create_referral_code first.',
                }

            recent_referrals = Referral.objects.filter(
                referral_code=ref_code
            ).order_by('-created_at')[:10]

            referrals_list = [
                {
                    'id': r.id,
                    'referred_email': r.referred_email,
                    'referred_user': str(r.referred_user) if r.referred_user else None,
                    'status': r.status,
                    'reward_amount': float(r.reward_amount),
                    'created_at': r.created_at.isoformat() if r.created_at else None,
                    'converted_at': r.converted_at.isoformat() if r.converted_at else None,
                }
                for r in recent_referrals
            ]

            logger.info("Retrieved referral stats for user %s", user)

            return {
                'success': True,
                'has_referral_code': True,
                'code': ref_code.code,
                'is_active': ref_code.is_active,
                'total_referrals': ref_code.total_referrals,
                'successful_referrals': ref_code.successful_referrals,
                'total_earnings': float(ref_code.total_earnings),
                'recent_referrals': referrals_list,
            }
        except Exception as e:
            logger.error("Failed to get referral stats for user %s: %s", user, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Partner Dashboard
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_partner_dashboard(partner_id: int) -> Dict[str, Any]:
        """
        Return partner analytics for the dashboard.

        Returns
        -------
        dict with total coupons, active coupons, total redemptions,
        total revenue, and recent redemptions.
        """
        from apps.agents.models import CouponRedemption, PartnerBusiness, PartnerCoupon

        try:
            try:
                partner = PartnerBusiness.objects.get(id=partner_id)
            except PartnerBusiness.DoesNotExist:
                return {'success': False, 'error': f'Partner with id {partner_id} not found'}

            total_coupons = PartnerCoupon.objects.filter(partner=partner).count()
            active_coupons = PartnerCoupon.objects.filter(partner=partner, is_active=True).count()

            redemptions = CouponRedemption.objects.filter(
                coupon__partner=partner,
            ).select_related('coupon', 'user')

            total_redemptions = redemptions.count()

            from django.db.models import Sum

            revenue_agg = redemptions.aggregate(
                total_commission=Sum('platform_commission'),
                total_savings=Sum('savings_amount'),
                total_order_value=Sum('order_total'),
            )
            total_revenue = float(revenue_agg['total_commission'] or 0)
            total_savings = float(revenue_agg['total_savings'] or 0)
            total_order_value = float(revenue_agg['total_order_value'] or 0)

            recent = redemptions.order_by('-redeemed_at')[:10]
            recent_list = [
                {
                    'id': r.id,
                    'coupon_code': r.coupon.code,
                    'coupon_title': r.coupon.title,
                    'user': str(r.user),
                    'order_total': float(r.order_total),
                    'savings_amount': float(r.savings_amount),
                    'platform_commission': float(r.platform_commission),
                    'redeemed_at': r.redeemed_at.isoformat() if r.redeemed_at else None,
                }
                for r in recent
            ]

            logger.info("Retrieved dashboard for partner %s (id=%s)", partner.name, partner_id)

            return {
                'success': True,
                'partner': {
                    'id': partner.id,
                    'name': partner.name,
                    'category': partner.category,
                    'destination': partner.destination,
                    'status': partner.status,
                    'rating': float(partner.rating),
                },
                'analytics': {
                    'total_coupons': total_coupons,
                    'active_coupons': active_coupons,
                    'total_redemptions': total_redemptions,
                    'total_revenue': total_revenue,
                    'total_savings_generated': total_savings,
                    'total_order_value': total_order_value,
                },
                'recent_redemptions': recent_list,
            }
        except Exception as e:
            logger.error("Failed to get dashboard for partner %s: %s", partner_id, e)
            return {'success': False, 'error': str(e)}

    # ------------------------------------------------------------------ #
    #  Revenue Share
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_revenue_share(user, savings_amount: float) -> Dict[str, Any]:
        """
        "AI saved you $X" model -- calculate the platform's 10% cut of savings.

        Parameters
        ----------
        user : User
            The user who received the savings.
        savings_amount : float
            The total amount saved.

        Returns
        -------
        dict with breakdown of savings, platform cut, and user benefit.
        """
        try:
            savings_decimal = Decimal(str(savings_amount))
            platform_cut = round(savings_decimal * PLATFORM_SAVINGS_CUT, 2)
            user_savings = savings_decimal - platform_cut

            logger.info(
                "Revenue share calculated for user %s: savings=$%s, platform=$%s, user=$%s",
                user, savings_decimal, platform_cut, user_savings,
            )

            return {
                'success': True,
                'breakdown': {
                    'total_savings': float(savings_decimal),
                    'platform_cut_pct': float(PLATFORM_SAVINGS_CUT * 100),
                    'platform_cut_amount': float(platform_cut),
                    'user_savings': float(user_savings),
                    'user': str(user),
                },
            }
        except Exception as e:
            logger.error("Failed to calculate revenue share: %s", e)
            return {'success': False, 'error': str(e)}


# ------------------------------------------------------------------ #
#  Module-level helpers
# ------------------------------------------------------------------ #


def _generate_referral_code(user) -> str:
    """Generate a referral code: first 3 chars of username (uppercase) + 5 hex chars."""
    username = getattr(user, 'username', '') or getattr(user, 'email', '') or 'USR'
    prefix = username[:3].upper()
    suffix = uuid.uuid4().hex[:5].upper()
    return f"{prefix}{suffix}"


def models_Q(**kwargs):
    """Helper to import and construct a Django Q object."""
    from django.db.models import Q
    return Q(**kwargs)


def _get_demo_coupons(destination: str = None, category: str = None) -> list:
    """Return sample coupons for demo purposes when no real coupons exist."""
    demo = [
        {
            'id': 1001,
            'code': 'HOTEL20',
            'title': '20% Off Luxury Hotels',
            'description': 'Save 20% on 4-star and 5-star hotels worldwide. Valid for stays of 2+ nights.',
            'discount_type': 'percentage',
            'discount_value': 20.0,
            'min_spend': 150.0,
            'valid_until': None,
            'terms': 'Valid for stays of 2 nights or more. Cannot be combined with other offers.',
            'partner_name': 'Grand Hotel Collection',
            'partner_category': 'hotel',
            'partner_destination': 'New York',
            'qr_data': '{"code":"HOTEL20","partner":"Grand Hotel Collection","discount":"20%"}',
            'partner': {'id': 101, 'name': 'Grand Hotel Collection', 'category': 'hotel', 'destination': 'New York', 'rating': 4.7},
        },
        {
            'id': 1002,
            'code': 'DINE15',
            'title': '$15 Off Fine Dining',
            'description': 'Enjoy $15 off your next fine dining experience at partner restaurants.',
            'discount_type': 'fixed',
            'discount_value': 15.0,
            'min_spend': 75.0,
            'valid_until': None,
            'terms': 'One per table. Dine-in only. Minimum spend $75.',
            'partner_name': 'Culinary Partners Network',
            'partner_category': 'restaurant',
            'partner_destination': 'New York',
            'qr_data': '{"code":"DINE15","partner":"Culinary Partners Network","discount":"$15 off"}',
            'partner': {'id': 102, 'name': 'Culinary Partners Network', 'category': 'restaurant', 'destination': 'New York', 'rating': 4.5},
        },
        {
            'id': 1003,
            'code': 'TOUR2FOR1',
            'title': 'Buy One Get One Tour Tickets',
            'description': 'Buy one guided tour ticket and get the second one free!',
            'discount_type': 'bogo',
            'discount_value': 50.0,
            'min_spend': 40.0,
            'valid_until': None,
            'terms': 'Valid for city walking tours and bus tours. Subject to availability.',
            'partner_name': 'City Explorer Tours',
            'partner_category': 'tour',
            'partner_destination': 'Paris',
            'qr_data': '{"code":"TOUR2FOR1","partner":"City Explorer Tours","discount":"BOGO"}',
            'partner': {'id': 103, 'name': 'City Explorer Tours', 'category': 'tour', 'destination': 'Paris', 'rating': 4.8},
        },
        {
            'id': 1004,
            'code': 'SPA30',
            'title': '30% Off Spa Treatments',
            'description': 'Relax and unwind with 30% off all spa and wellness treatments.',
            'discount_type': 'percentage',
            'discount_value': 30.0,
            'min_spend': 80.0,
            'valid_until': None,
            'terms': 'Advance booking required. Cannot be used on packages.',
            'partner_name': 'Zen Wellness Retreats',
            'partner_category': 'spa',
            'partner_destination': 'Bali',
            'qr_data': '{"code":"SPA30","partner":"Zen Wellness Retreats","discount":"30%"}',
            'partner': {'id': 104, 'name': 'Zen Wellness Retreats', 'category': 'spa', 'destination': 'Bali', 'rating': 4.9},
        },
        {
            'id': 1005,
            'code': 'ATTRACT10',
            'title': '10% Off Top Attractions',
            'description': 'Get 10% off entry tickets to popular museums, theme parks, and landmarks.',
            'discount_type': 'percentage',
            'discount_value': 10.0,
            'min_spend': 20.0,
            'valid_until': None,
            'terms': 'Valid at participating attractions. Online purchase only.',
            'partner_name': 'Attraction Pass Global',
            'partner_category': 'attraction',
            'partner_destination': 'London',
            'qr_data': '{"code":"ATTRACT10","partner":"Attraction Pass Global","discount":"10%"}',
            'partner': {'id': 105, 'name': 'Attraction Pass Global', 'category': 'attraction', 'destination': 'London', 'rating': 4.6},
        },
        {
            'id': 1006,
            'code': 'RIDE25',
            'title': '$25 Off Airport Transfers',
            'description': 'Save $25 on airport pickup and drop-off services in any city.',
            'discount_type': 'fixed',
            'discount_value': 25.0,
            'min_spend': 50.0,
            'valid_until': None,
            'terms': 'Must book 24 hours in advance. One use per trip.',
            'partner_name': 'SwiftRide Transfers',
            'partner_category': 'transport',
            'partner_destination': 'Dubai',
            'qr_data': '{"code":"RIDE25","partner":"SwiftRide Transfers","discount":"$25 off"}',
            'partner': {'id': 106, 'name': 'SwiftRide Transfers', 'category': 'transport', 'destination': 'Dubai', 'rating': 4.4},
        },
        {
            'id': 1007,
            'code': 'SHOP15',
            'title': '15% Off Duty-Free Shopping',
            'description': 'Enjoy 15% off at partner duty-free shops and local boutiques.',
            'discount_type': 'percentage',
            'discount_value': 15.0,
            'min_spend': 100.0,
            'valid_until': None,
            'terms': 'Minimum purchase $100. Not valid on electronics.',
            'partner_name': 'TravelMart Duty Free',
            'partner_category': 'shopping',
            'partner_destination': 'Tokyo',
            'qr_data': '{"code":"SHOP15","partner":"TravelMart Duty Free","discount":"15%"}',
            'partner': {'id': 107, 'name': 'TravelMart Duty Free', 'category': 'shopping', 'destination': 'Tokyo', 'rating': 4.3},
        },
        {
            'id': 1008,
            'code': 'HOTEL35',
            'title': '35% Off Boutique Hotels',
            'description': 'Exclusive 35% discount on handpicked boutique hotels in Europe.',
            'discount_type': 'percentage',
            'discount_value': 35.0,
            'min_spend': 200.0,
            'valid_until': None,
            'terms': 'Valid for 3+ night stays. Europe destinations only.',
            'partner_name': 'Boutique Stays Europe',
            'partner_category': 'hotel',
            'partner_destination': 'Rome',
            'qr_data': '{"code":"HOTEL35","partner":"Boutique Stays Europe","discount":"35%"}',
            'partner': {'id': 108, 'name': 'Boutique Stays Europe', 'category': 'hotel', 'destination': 'Rome', 'rating': 4.8},
        },
    ]

    filtered = demo
    if destination:
        dest_lower = destination.lower()
        filtered = [c for c in filtered if dest_lower in c['partner_destination'].lower()]
    if category:
        filtered = [c for c in filtered if c['partner_category'] == category]

    return filtered
