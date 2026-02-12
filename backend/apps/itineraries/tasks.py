"""
Celery tasks for itinerary operations.
"""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile
import io
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_weather_data(self, itinerary_id=None):
    """
    Update weather forecast data for itineraries.

    Args:
        itinerary_id: Optional specific itinerary ID. If None, updates all active itineraries.
    """
    try:
        from .models import Itinerary, ItineraryDay
        from apps.agents.integrations.weather_client import WeatherClient
        from datetime import timedelta

        logger.info(f"Starting weather data update for itinerary: {itinerary_id or 'all'}")

        # Determine which itineraries to update
        if itinerary_id:
            itineraries = Itinerary.objects.filter(id=itinerary_id)
        else:
            # Update itineraries starting within next 14 days
            cutoff_date = timezone.now().date() + timedelta(days=14)
            itineraries = Itinerary.objects.filter(
                start_date__lte=cutoff_date,
                start_date__gte=timezone.now().date(),
                status='active'
            )

        weather_client = WeatherClient()
        updated_count = 0

        for itinerary in itineraries:
            try:
                # Get weather for each day of the itinerary
                itinerary_days = ItineraryDay.objects.filter(
                    itinerary=itinerary
                ).order_by('date')

                for day in itinerary_days:
                    try:
                        # Fetch weather forecast
                        weather_data = weather_client.get_forecast(
                            latitude=day.latitude,
                            longitude=day.longitude,
                            date=day.date
                        )

                        # Update day with weather data
                        day.weather_data = weather_data
                        day.temperature_high = weather_data.get('temp_high')
                        day.temperature_low = weather_data.get('temp_low')
                        day.weather_condition = weather_data.get('condition')
                        day.precipitation_chance = weather_data.get('precipitation_probability')
                        day.save()

                        logger.debug(f"Weather updated for itinerary {itinerary.id}, day {day.date}")

                    except Exception as e:
                        logger.error(f"Error updating weather for day {day.id}: {str(e)}")
                        continue

                # Update itinerary last updated timestamp
                itinerary.weather_updated_at = timezone.now()
                itinerary.save(update_fields=['weather_updated_at'])

                updated_count += 1
                logger.info(f"Weather data updated for itinerary {itinerary.id}")

            except Exception as e:
                logger.error(f"Error updating weather for itinerary {itinerary.id}: {str(e)}")
                continue

        logger.info(f"Weather update completed. {updated_count} itineraries updated.")

        return {
            'status': 'success',
            'itineraries_updated': updated_count
        }

    except Exception as exc:
        logger.error(f"Error in update_weather_data task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_itinerary_pdf(self, itinerary_id):
    """
    Generate a PDF document for an itinerary.

    Args:
        itinerary_id: ID of the itinerary to generate PDF for
    """
    try:
        from .models import Itinerary, ItineraryDay
        from apps.notifications.models import Notification

        logger.info(f"Generating PDF for itinerary {itinerary_id}")

        try:
            itinerary = Itinerary.objects.select_related('user').get(id=itinerary_id)
        except Itinerary.DoesNotExist:
            logger.error(f"Itinerary {itinerary_id} not found")
            return {'status': 'error', 'message': 'Itinerary not found'}

        # Get all itinerary data
        days = ItineraryDay.objects.filter(
            itinerary=itinerary
        ).order_by('date').prefetch_related('activities', 'accommodations')

        try:
            # Generate PDF using reportlab or weasyprint
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib import colors

            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a73e8'),
                spaceAfter=30,
            )
            story.append(Paragraph(f"Travel Itinerary: {itinerary.title}", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Itinerary details
            details_data = [
                ['Destination:', itinerary.destination],
                ['Start Date:', itinerary.start_date.strftime('%B %d, %Y')],
                ['End Date:', itinerary.end_date.strftime('%B %d, %Y')],
                ['Duration:', f"{itinerary.duration_days} days"],
            ]

            details_table = Table(details_data, colWidths=[2*inch, 4*inch])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ]))
            story.append(details_table)
            story.append(Spacer(1, 0.3 * inch))

            # Daily itinerary
            for day in days:
                # Day header
                day_style = ParagraphStyle(
                    'DayHeader',
                    parent=styles['Heading2'],
                    fontSize=16,
                    textColor=colors.HexColor('#1a73e8'),
                    spaceAfter=12,
                )
                story.append(Paragraph(
                    f"Day {day.day_number} - {day.date.strftime('%A, %B %d, %Y')}",
                    day_style
                ))

                # Location
                if day.location:
                    story.append(Paragraph(f"<b>Location:</b> {day.location}", styles['Normal']))

                # Weather
                if day.weather_condition:
                    weather_text = f"<b>Weather:</b> {day.weather_condition}"
                    if day.temperature_high and day.temperature_low:
                        weather_text += f" (High: {day.temperature_high}°F, Low: {day.temperature_low}°F)"
                    story.append(Paragraph(weather_text, styles['Normal']))

                # Activities
                if day.activities.exists():
                    story.append(Paragraph("<b>Activities:</b>", styles['Normal']))
                    for activity in day.activities.all():
                        activity_text = f"• {activity.name}"
                        if activity.start_time:
                            activity_text += f" - {activity.start_time.strftime('%I:%M %p')}"
                        story.append(Paragraph(activity_text, styles['Normal']))

                # Notes
                if day.notes:
                    story.append(Paragraph(f"<b>Notes:</b> {day.notes}", styles['Normal']))

                story.append(Spacer(1, 0.3 * inch))

            # Build PDF
            doc.build(story)

            # Save PDF to itinerary
            pdf_content = buffer.getvalue()
            buffer.close()

            filename = f"itinerary_{itinerary.id}_{timezone.now().strftime('%Y%m%d')}.pdf"
            itinerary.pdf_file.save(
                filename,
                ContentFile(pdf_content),
                save=True
            )

            # Update generation timestamp
            itinerary.pdf_generated_at = timezone.now()
            itinerary.save(update_fields=['pdf_generated_at'])

            # Notify user
            Notification.objects.create(
                user=itinerary.user,
                notification_type='itinerary_pdf_ready',
                title='Your Itinerary PDF is Ready',
                message=f'Your itinerary "{itinerary.title}" has been generated and is ready to download.',
                data={
                    'itinerary_id': itinerary.id,
                    'pdf_url': itinerary.pdf_file.url if itinerary.pdf_file else None
                }
            )

            logger.info(f"PDF generated successfully for itinerary {itinerary_id}")

            return {
                'status': 'success',
                'itinerary_id': itinerary_id,
                'pdf_url': itinerary.pdf_file.url if itinerary.pdf_file else None
            }

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise

    except Exception as exc:
        logger.error(f"Error in generate_itinerary_pdf task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def optimize_itinerary_route(self, itinerary_id):
    """
    Optimize the route order of activities in an itinerary to minimize travel time.

    Args:
        itinerary_id: ID of the itinerary to optimize
    """
    try:
        from .models import Itinerary, ItineraryDay
        from apps.agents.integrations.maps_client import MapsClient

        logger.info(f"Optimizing route for itinerary {itinerary_id}")

        try:
            itinerary = Itinerary.objects.get(id=itinerary_id)
        except Itinerary.DoesNotExist:
            logger.error(f"Itinerary {itinerary_id} not found")
            return {'status': 'error', 'message': 'Itinerary not found'}

        maps_client = MapsClient()
        days_optimized = 0

        # Optimize each day
        days = ItineraryDay.objects.filter(itinerary=itinerary).order_by('date')

        for day in days:
            activities = list(day.activities.all().order_by('start_time'))

            if len(activities) < 2:
                continue  # Nothing to optimize

            try:
                # Get coordinates for all activities
                waypoints = [
                    {'lat': activity.latitude, 'lng': activity.longitude, 'id': activity.id}
                    for activity in activities
                    if activity.latitude and activity.longitude
                ]

                if len(waypoints) < 2:
                    continue

                # Calculate optimal route
                optimized_route = maps_client.optimize_route(waypoints)

                # Reorder activities based on optimized route
                for idx, activity_id in enumerate(optimized_route['order']):
                    activity = next(a for a in activities if a.id == activity_id)
                    activity.order = idx
                    activity.save(update_fields=['order'])

                # Update day with route info
                day.total_travel_distance = optimized_route.get('total_distance')
                day.total_travel_time = optimized_route.get('total_duration')
                day.save()

                days_optimized += 1
                logger.info(f"Route optimized for day {day.id}")

            except Exception as e:
                logger.error(f"Error optimizing route for day {day.id}: {str(e)}")
                continue

        logger.info(f"Route optimization completed for itinerary {itinerary_id}. {days_optimized} days optimized.")

        return {
            'status': 'success',
            'itinerary_id': itinerary_id,
            'days_optimized': days_optimized
        }

    except Exception as exc:
        logger.error(f"Error in optimize_itinerary_route task: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3)
def send_itinerary_email_task(
    self,
    itinerary_id: int,
    to_email: str,
    subject: str = None,
    backend: str = 'auto',
    include_calendar: bool = False,
    theme: str = 'pumpkin'
):
    """
    Async task to generate PDF and send itinerary email.

    Args:
        itinerary_id: ID of the itinerary to send
        to_email: Recipient email address
        subject: Optional custom subject
        backend: Email backend to use
        include_calendar: Whether to include .ics file
        theme: PDF theme

    Returns:
        dict with status and message
    """
    try:
        from .models import Itinerary
        from .pdf_generator import ProfessionalPDFGenerator
        from .email_service import EmailService, CalendarService

        # Get itinerary
        itinerary = Itinerary.objects.select_related('user').prefetch_related(
            'days__items'
        ).get(id=itinerary_id)

        # Generate subject if not provided
        if not subject:
            subject = f'Your Trip Itinerary: {itinerary.destination}'

        # Generate itinerary text
        itinerary_text = _generate_itinerary_text(itinerary)

        # Create PDF
        media_root = Path(settings.MEDIA_ROOT) / 'pdfs'
        media_root.mkdir(parents=True, exist_ok=True)

        clean_dest = itinerary.destination.replace(" ", "_").replace("/", "_")[:30]
        filename = f"itinerary_{clean_dest}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = str(media_root / filename)

        # Generate PDF
        ProfessionalPDFGenerator.create_itinerary_pdf(
            itinerary_text=itinerary_text,
            destination=itinerary.destination,
            dates=f"{itinerary.start_date} to {itinerary.end_date}",
            origin=itinerary.origin or "N/A",
            budget=int(itinerary.total_budget) if itinerary.total_budget else 0,
            output_path=pdf_path,
            theme=theme,
            user_name=itinerary.user.get_full_name() or itinerary.user.username
        )

        # Generate calendar file if requested
        ics_path = None
        if include_calendar:
            ics_path = str(media_root / f"itinerary_{clean_dest}.ics")
            activities = []
            for day in itinerary.days.all():
                for item in day.items.all():
                    if item.start_time:
                        activities.append({
                            'title': item.title,
                            'time': datetime.combine(day.date, item.start_time),
                            'description': item.description or ''
                        })

            CalendarService.create_ics_file(
                destination=itinerary.destination,
                start_date=str(itinerary.start_date),
                end_date=str(itinerary.end_date),
                activities=activities,
                output_path=ics_path
            )

        # Send email
        success = EmailService.send_itinerary_email(
            to_email=to_email,
            subject=subject,
            itinerary_text=itinerary_text,
            pdf_path=pdf_path,
            user_name=itinerary.user.get_full_name() or itinerary.user.username,
            destination=itinerary.destination,
            dates=f"{itinerary.start_date} to {itinerary.end_date}",
            backend=backend
        )

        if success:
            logger.info(f"Email sent successfully for itinerary {itinerary_id} to {to_email}")
            return {
                'status': 'success',
                'message': f'Email sent to {to_email}',
                'pdf_filename': filename
            }
        else:
            logger.error(f"Email sending failed for itinerary {itinerary_id}")
            raise Exception("Email sending failed")

    except Exception as exc:
        logger.error(f"Error sending email for itinerary {itinerary_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def cleanup_old_pdfs_task(days_old: int = 7):
    """
    Clean up PDF files older than specified days.

    Args:
        days_old: Delete PDFs older than this many days
    """
    try:
        import time

        pdf_dir = Path(settings.MEDIA_ROOT) / 'pdfs'
        if not pdf_dir.exists():
            return {'status': 'success', 'deleted': 0}

        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)

        deleted_count = 0
        for pdf_file in pdf_dir.glob('*.pdf'):
            if pdf_file.stat().st_mtime < cutoff_time:
                pdf_file.unlink()
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old PDF files")

        return {
            'status': 'success',
            'deleted': deleted_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up PDFs: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


def _generate_itinerary_text(itinerary):
    """Helper function to generate markdown-formatted itinerary text"""
    lines = []

    # Title and metadata
    lines.append(f"# {itinerary.title or itinerary.destination}")
    lines.append(f"\n**Destination:** {itinerary.destination}")
    lines.append(f"**Dates:** {itinerary.start_date} to {itinerary.end_date}")
    lines.append(f"**Budget:** ${itinerary.total_budget}")
    lines.append("")

    # Add itinerary overview if available
    if itinerary.notes:
        lines.append("## Overview")
        lines.append(itinerary.notes)
        lines.append("")

    # Day-by-day itinerary
    days = itinerary.days.all().order_by('day_number')
    for day in days:
        lines.append(f"## Day {day.day_number}: {day.title or 'Activities'}")
        if day.notes:
            lines.append(day.notes)

        # Add items for this day
        items = day.items.all().order_by('order', 'start_time')
        for item in items:
            if item.start_time:
                time_str = item.start_time.strftime('%I:%M %p')
                lines.append(f"{time_str} - {item.title}")
            else:
                lines.append(f"- {item.title}")

            if item.description:
                lines.append(f"  {item.description}")

            if item.location:
                lines.append(f"  📍 {item.location}")

            if item.estimated_cost:
                lines.append(f"  💰 ${item.estimated_cost}")

        lines.append("")

    return "\n".join(lines)
