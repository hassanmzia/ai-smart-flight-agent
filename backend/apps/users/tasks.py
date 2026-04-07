"""
Celery tasks for user operations.
"""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=3600)
def cleanup_expired_sessions(self):
    """
    Clean up expired user sessions and temporary data.
    Runs periodically to maintain database hygiene.
    """
    try:
        from django.contrib.sessions.models import Session

        logger.info("Starting expired sessions cleanup")

        # Delete expired sessions
        expired_sessions = Session.objects.filter(
            expire_date__lt=timezone.now()
        )
        deleted_count = expired_sessions.count()
        expired_sessions.delete()

        logger.info(f"Deleted {deleted_count} expired sessions")

        # Clean up expired password reset tokens
        from django.contrib.auth.tokens import default_token_generator
        from .models import User

        # Delete unverified users older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        unverified_users = User.objects.filter(
            is_active=False,
            is_verified=False,
            date_joined__lt=cutoff_date
        )
        unverified_count = unverified_users.count()
        unverified_users.delete()

        logger.info(f"Deleted {unverified_count} unverified user accounts")

        return {
            'status': 'success',
            'expired_sessions_deleted': deleted_count,
            'unverified_users_deleted': unverified_count
        }

    except Exception as exc:
        logger.error(f"Error in cleanup_expired_sessions task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def send_welcome_email(self, user_id):
    """
    Send welcome email to newly registered user.

    Args:
        user_id: ID of the user to send welcome email to
    """
    try:
        from .models import User

        logger.info(f"Sending welcome email to user {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        if not user.email:
            logger.warning(f"User {user_id} has no email address")
            return {'status': 'error', 'message': 'No email address'}

        try:
            # Prepare email context
            context = {
                'user': user,
                'site_name': settings.SITE_NAME,
                'site_url': settings.SITE_URL,
                'support_email': settings.SUPPORT_EMAIL,
            }

            # Render email templates
            html_message = render_to_string('emails/welcome_email.html', context)
            text_message = render_to_string('emails/welcome_email.txt', context)

            # Send email
            send_mail(
                subject=f'Welcome to {settings.SITE_NAME}!',
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )

            # Update user record
            user.welcome_email_sent = True
            user.welcome_email_sent_at = timezone.now()
            user.save(update_fields=['welcome_email_sent', 'welcome_email_sent_at'])

            logger.info(f"Welcome email sent successfully to user {user_id}")

            return {
                'status': 'success',
                'user_id': user_id,
                'email': user.email
            }

        except Exception as e:
            logger.error(f"Error sending welcome email: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"Error in send_welcome_email task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, reset_token):
    """
    Send password reset email to user.

    Args:
        user_id: ID of the user
        reset_token: Password reset token
    """
    try:
        from .models import User

        logger.info(f"Sending password reset email to user {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        # Generate reset URL
        reset_url = f"{settings.SITE_URL}/reset-password/{reset_token}"

        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': settings.SITE_NAME,
            'valid_hours': 24,
        }

        html_message = render_to_string('emails/password_reset.html', context)
        text_message = render_to_string('emails/password_reset.txt', context)

        send_mail(
            subject='Password Reset Request',
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

        logger.info(f"Password reset email sent to user {user_id}")

        return {
            'status': 'success',
            'user_id': user_id
        }

    except Exception as exc:
        logger.error(f"Error in send_password_reset_email task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def update_user_loyalty_points(self, user_id, points, reason):
    """
    Update user loyalty points and send notification.

    Args:
        user_id: ID of the user
        points: Points to add (positive) or deduct (negative)
        reason: Reason for points change
    """
    try:
        from .models import User, LoyaltyTransaction
        from apps.notifications.models import Notification

        logger.info(f"Updating loyalty points for user {user_id}: {points} points")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        # Record transaction
        transaction = LoyaltyTransaction.objects.create(
            user=user,
            points=points,
            reason=reason,
            balance_before=user.loyalty_points,
            balance_after=user.loyalty_points + points
        )

        # Update user points
        user.loyalty_points += points
        user.save(update_fields=['loyalty_points'])

        # Send notification
        if points > 0:
            message = f'You earned {points} loyalty points! {reason}'
        else:
            message = f'{abs(points)} loyalty points were redeemed. {reason}'

        Notification.objects.create(
            user=user,
            notification_type='loyalty_update',
            title='Loyalty Points Update',
            message=message,
            data={
                'points': points,
                'new_balance': user.loyalty_points,
                'reason': reason
            }
        )

        logger.info(f"Loyalty points updated for user {user_id}. New balance: {user.loyalty_points}")

        return {
            'status': 'success',
            'user_id': user_id,
            'points_changed': points,
            'new_balance': user.loyalty_points
        }

    except Exception as exc:
        logger.error(f"Error in update_user_loyalty_points task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_account_verification_email(self, user_id, verification_token):
    """
    Send email verification link to user.

    Args:
        user_id: ID of the user
        verification_token: Email verification token
    """
    try:
        from .models import User

        logger.info(f"Sending verification email to user {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        # Generate verification URL
        verification_url = f"{settings.SITE_URL}/verify-email/{verification_token}"

        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': settings.SITE_NAME,
        }

        html_message = render_to_string('emails/email_verification.html', context)
        text_message = render_to_string('emails/email_verification.txt', context)

        send_mail(
            subject='Verify Your Email Address',
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )

        logger.info(f"Verification email sent to user {user_id}")

        return {
            'status': 'success',
            'user_id': user_id
        }

    except Exception as exc:
        logger.error(f"Error in send_account_verification_email task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def generate_user_activity_report(self, user_id, start_date, end_date):
    """
    Generate activity report for a user.

    Args:
        user_id: ID of the user
        start_date: Start date for report (ISO format)
        end_date: End date for report (ISO format)
    """
    try:
        from .models import User
        from apps.bookings.models import Booking
        from apps.payments.models import Payment
        from datetime import datetime

        logger.info(f"Generating activity report for user {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found")
            return {'status': 'error', 'message': 'User not found'}

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        # Gather statistics
        bookings = Booking.objects.filter(
            user=user,
            created_at__gte=start,
            created_at__lte=end
        )

        payments = Payment.objects.filter(
            user=user,
            created_at__gte=start,
            created_at__lte=end,
            status='completed'
        )

        report = {
            'user_id': user_id,
            'period': {
                'start': start_date,
                'end': end_date
            },
            'bookings': {
                'total': bookings.count(),
                'confirmed': bookings.filter(status='confirmed').count(),
                'cancelled': bookings.filter(status='cancelled').count(),
            },
            'payments': {
                'total': payments.count(),
                'total_amount': float(sum(p.amount for p in payments)),
            },
            'loyalty_points': user.loyalty_points,
        }

        logger.info(f"Activity report generated for user {user_id}")

        return {
            'status': 'success',
            'report': report
        }

    except Exception as exc:
        logger.error(f"Error in generate_user_activity_report task: {str(exc)}")
        raise self.retry(exc=exc)
