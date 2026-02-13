import os
from pathlib import Path
from datetime import datetime

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse, HttpResponse
from django.conf import settings

from .models import Itinerary, ItineraryDay, ItineraryItem, Weather
from .serializers import (
    ItinerarySerializer, ItineraryDaySerializer,
    ItineraryItemSerializer, WeatherSerializer
)
from .pdf_generator import ProfessionalPDFGenerator
from .email_service import EmailService, CalendarService


class ItineraryViewSet(viewsets.ModelViewSet):
    """ViewSet for Itinerary model."""
    queryset = Itinerary.objects.all()
    serializer_class = ItinerarySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'destination']
    filterset_fields = ['status', 'destination']
    ordering = ['-start_date']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Itinerary.objects.all()
        return Itinerary.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def _generate_itinerary_text(self, itinerary):
        """Generate markdown-formatted itinerary text from database model.

        If the itinerary has a stored AI narrative (from the AI planner),
        use that directly for full-fidelity PDF export including all
        details like Getting-there directions, restaurant names, weather,
        safety tips, budget summary, and packing list.
        """
        # Use stored AI narrative if available — it has the full rich plan
        if itinerary.ai_narrative and itinerary.ai_narrative.strip():
            return itinerary.ai_narrative

        lines = []

        # Title
        lines.append(f"# {itinerary.title or itinerary.destination}")
        lines.append("")

        # Add itinerary overview if available
        if itinerary.description:
            lines.append("## Trip Overview")
            lines.append(itinerary.description)
            lines.append("")

        # Day-by-day itinerary
        days = itinerary.days.all().order_by('day_number')
        if days.exists():
            for day in days:
                day_label = day.title or "Activities"
                date_str = ""
                if day.date:
                    date_str = f" ({day.date.strftime('%A, %B %d, %Y')})"
                lines.append(f"## Day {day.day_number}: {day_label}{date_str}")
                lines.append("")

                if day.notes:
                    lines.append(day.notes)
                    lines.append("")

                # Group items by type for a nice table
                items = day.items.all().order_by('order', 'start_time')
                if items.exists():
                    # Build a markdown table for the day's items
                    lines.append("| Time | Type | Activity | Location | Cost |")
                    lines.append("|------|------|----------|----------|------|")
                    for item in items:
                        time_str = item.start_time.strftime('%I:%M %p') if item.start_time else "Flexible"
                        item_type = item.item_type.replace('_', ' ').title() if item.item_type else ""
                        title = item.title or ""
                        if item.description:
                            title += f" - {item.description}"
                        location = item.location_name or ""
                        if item.location_address and item.location_address != item.location_name:
                            location += f" ({item.location_address})" if location else item.location_address
                        cost = f"${item.estimated_cost:.0f}" if item.estimated_cost else "-"
                        lines.append(f"| {time_str} | {item_type} | {title} | {location} | {cost} |")
                    lines.append("")

                    # Also add any items with URLs as references
                    url_items = [item for item in items if item.url]
                    if url_items:
                        lines.append("### Booking Links")
                        for item in url_items:
                            lines.append(f"- {item.title}: {item.url}")
                        lines.append("")

                    # Day cost summary
                    day_costs = [item.estimated_cost for item in items if item.estimated_cost]
                    if day_costs:
                        lines.append(f"**Day {day.day_number} Estimated Cost:** ${sum(day_costs):.0f}")
                        lines.append("")
                else:
                    lines.append("No activities planned yet for this day.")
                    lines.append("")

        # Budget Summary
        total_cost = 0
        for day in days:
            for item in day.items.all():
                if item.estimated_cost:
                    total_cost += float(item.estimated_cost)

        if total_cost > 0:
            lines.append("## Budget Summary")
            budget_val = float(itinerary.estimated_budget) if itinerary.estimated_budget else 0
            lines.append(f"- **Total Estimated Cost:** ${total_cost:.0f} {itinerary.currency or 'USD'}")
            if budget_val > 0:
                lines.append(f"- **Planned Budget:** ${budget_val:.0f} {itinerary.currency or 'USD'}")
                remaining = budget_val - total_cost
                if remaining >= 0:
                    lines.append(f"- **Remaining Budget:** ${remaining:.0f}")
                else:
                    lines.append(f"- **Over Budget By:** ${abs(remaining):.0f}")
            lines.append("")

        # Travelers info
        if itinerary.number_of_travelers and itinerary.number_of_travelers > 0:
            lines.append(f"**Travelers:** {itinerary.number_of_travelers}")
            lines.append("")

        return "\n".join(lines)

    @action(detail=True, methods=['get', 'post'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        """
        Export itinerary as professional PDF.

        GET: Download PDF
        POST: Generate PDF with custom options

        POST body options:
        - theme: "pumpkin", "ocean", or "forest" (default: "pumpkin")
        - include_qr: boolean (default: false)
        - format: "download" or "inline" (default: "download")
        """
        itinerary = self.get_object()

        # Get options from POST or use defaults
        theme = request.data.get('theme', 'pumpkin') if request.method == 'POST' else 'pumpkin'
        include_qr = request.data.get('include_qr', False) if request.method == 'POST' else False
        format_type = request.data.get('format', 'download') if request.method == 'POST' else 'download'

        # Generate itinerary text
        itinerary_text = self._generate_itinerary_text(itinerary)

        # Create PDF file path
        media_root = Path(settings.MEDIA_ROOT) / 'pdfs'
        media_root.mkdir(parents=True, exist_ok=True)

        clean_dest = itinerary.destination.replace(" ", "_").replace("/", "_")[:30]
        filename = f"itinerary_{clean_dest}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = str(media_root / filename)

        # Generate QR code URL if requested
        qr_url = None
        if include_qr:
            qr_url = f"{request.scheme}://{request.get_host()}/itineraries/{itinerary.id}/"

        try:
            # Generate PDF
            ProfessionalPDFGenerator.create_itinerary_pdf(
                itinerary_text=itinerary_text,
                destination=itinerary.destination,
                dates=f"{itinerary.start_date} to {itinerary.end_date}",
                origin="N/A",
                budget=int(itinerary.estimated_budget) if itinerary.estimated_budget else 0,
                output_path=pdf_path,
                theme=theme,
                user_name=request.user.get_full_name() or request.user.username,
                include_qr=include_qr,
                qr_url=qr_url
            )

            # Return PDF file
            pdf_file = open(pdf_path, 'rb')

            if format_type == 'inline':
                response = FileResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{filename}"'
            else:
                response = FileResponse(pdf_file, content_type='application/pdf', as_attachment=True)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            return Response(
                {'error': f'PDF generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='send-email')
    def send_email(self, request, pk=None):
        """
        Send itinerary PDF via email.

        POST body:
        - to_email: recipient email address (required)
        - subject: custom email subject (optional)
        - backend: "auto", "django", "smtp", "sendgrid", or "ses" (default: "auto")
        - include_calendar: boolean (default: false)
        """
        itinerary = self.get_object()

        # Get email parameters
        to_email = request.data.get('to_email')
        if not to_email:
            return Response(
                {'error': 'to_email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = request.data.get('subject', f'Your Trip Itinerary: {itinerary.destination}')
        backend = request.data.get('backend', 'auto')
        include_calendar = request.data.get('include_calendar', False)

        # Generate itinerary text
        itinerary_text = self._generate_itinerary_text(itinerary)

        # Create PDF
        media_root = Path(settings.MEDIA_ROOT) / 'pdfs'
        media_root.mkdir(parents=True, exist_ok=True)

        clean_dest = itinerary.destination.replace(" ", "_").replace("/", "_")[:30]
        filename = f"itinerary_{clean_dest}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = str(media_root / filename)

        try:
            # Generate PDF
            ProfessionalPDFGenerator.create_itinerary_pdf(
                itinerary_text=itinerary_text,
                destination=itinerary.destination,
                dates=f"{itinerary.start_date} to {itinerary.end_date}",
                origin="N/A",
                budget=int(itinerary.estimated_budget) if itinerary.estimated_budget else 0,
                output_path=pdf_path,
                user_name=request.user.get_full_name() or request.user.username
            )

            # Generate calendar file if requested
            ics_path = None
            if include_calendar:
                ics_path = str(media_root / f"itinerary_{clean_dest}.ics")
                # Extract activities for calendar
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
                user_name=request.user.get_full_name() or request.user.username,
                destination=itinerary.destination,
                dates=f"{itinerary.start_date} to {itinerary.end_date}",
                backend=backend
            )

            if success:
                return Response({
                    'message': f'Email sent successfully to {to_email}',
                    'pdf_filename': filename
                })
            else:
                return Response(
                    {'error': 'Email sending failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {'error': f'Email sending failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], url_path='export-calendar')
    def export_calendar(self, request, pk=None):
        """Export itinerary as .ics calendar file"""
        itinerary = self.get_object()

        # Create calendar file
        media_root = Path(settings.MEDIA_ROOT) / 'calendars'
        media_root.mkdir(parents=True, exist_ok=True)

        clean_dest = itinerary.destination.replace(" ", "_").replace("/", "_")[:30]
        filename = f"itinerary_{clean_dest}.ics"
        ics_path = str(media_root / filename)

        # Extract activities
        activities = []
        for day in itinerary.days.all():
            for item in day.items.all():
                if item.start_time:
                    activities.append({
                        'title': item.title,
                        'time': datetime.combine(day.date, item.start_time),
                        'description': item.description or ''
                    })

        try:
            CalendarService.create_ics_file(
                destination=itinerary.destination,
                start_date=str(itinerary.start_date),
                end_date=str(itinerary.end_date),
                activities=activities,
                output_path=ics_path
            )

            # Return calendar file
            ics_file = open(ics_path, 'rb')
            response = FileResponse(ics_file, content_type='text/calendar', as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            return Response(
                {'error': f'Calendar generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # ── Status Workflow Endpoints ──

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve an itinerary plan — moves from planned → approved."""
        itinerary = self.get_object()
        if itinerary.status not in ('planned', 'draft'):
            return Response(
                {'error': f'Cannot approve an itinerary with status "{itinerary.status}". Must be planned or draft.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        itinerary.status = 'approved'
        itinerary.save(update_fields=['status', 'updated_at'])
        return Response({
            'success': True,
            'status': 'approved',
            'message': 'Itinerary approved! You can now proceed to book.',
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject / send back to draft for edits."""
        itinerary = self.get_object()
        reason = request.data.get('reason', '')
        itinerary.status = 'draft'
        itinerary.save(update_fields=['status', 'updated_at'])
        return Response({
            'success': True,
            'status': 'draft',
            'message': f'Itinerary sent back to draft.{" Reason: " + reason if reason else ""}',
        })

    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        """
        ReAct Booking Agent — takes an approved itinerary and books everything.

        This simulates the booking process for flights, hotels, car rentals,
        restaurants, and attractions. In a production system, this would
        connect to real booking APIs (Amadeus, Booking.com, etc.).

        Flow: approved → booking → booked
        """
        import uuid as _uuid
        import logging
        logger = logging.getLogger(__name__)

        itinerary = self.get_object()
        if itinerary.status != 'approved':
            return Response(
                {'error': f'Cannot book an itinerary with status "{itinerary.status}". Must be approved first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as booking in progress
        itinerary.status = 'booking'
        itinerary.save(update_fields=['status', 'updated_at'])

        booking_results = []
        total_booked_cost = 0
        errors = []

        try:
            # ── Step 1: Book all itinerary items ──
            items = ItineraryItem.objects.filter(
                day__itinerary=itinerary
            ).select_related('day').order_by('day__day_number', 'order')

            for item in items:
                if item.is_booked:
                    booking_results.append({
                        'item': item.title,
                        'type': item.item_type,
                        'status': 'already_booked',
                        'reference': item.booking_reference,
                    })
                    continue

                # Generate booking reference
                ref = f"BK-{item.item_type[:3].upper()}-{_uuid.uuid4().hex[:8].upper()}"

                # Simulate booking based on item type
                try:
                    if item.item_type == 'flight':
                        # In production: call Amadeus/Skyscanner booking API
                        item.is_booked = True
                        item.booking_reference = ref
                        item.notes = (item.notes or '') + f'\nBooked: {ref}'
                        item.save()
                        cost = float(item.estimated_cost or 0)
                        total_booked_cost += cost
                        booking_results.append({
                            'item': item.title,
                            'type': 'flight',
                            'status': 'booked',
                            'reference': ref,
                            'cost': cost,
                        })

                    elif item.item_type == 'hotel':
                        # In production: call Booking.com/Hotels.com API
                        item.is_booked = True
                        item.booking_reference = ref
                        item.notes = (item.notes or '') + f'\nBooked: {ref}'
                        item.save()
                        cost = float(item.estimated_cost or 0)
                        total_booked_cost += cost
                        booking_results.append({
                            'item': item.title,
                            'type': 'hotel',
                            'status': 'booked',
                            'reference': ref,
                            'cost': cost,
                        })

                    elif item.item_type == 'restaurant':
                        # In production: call OpenTable/Resy API for reservation
                        item.is_booked = True
                        item.booking_reference = ref
                        item.notes = (item.notes or '') + f'\nReservation: {ref}'
                        item.save()
                        cost = float(item.estimated_cost or 0)
                        total_booked_cost += cost
                        booking_results.append({
                            'item': item.title,
                            'type': 'restaurant',
                            'status': 'reserved',
                            'reference': ref,
                            'cost': cost,
                        })

                    elif item.item_type == 'attraction':
                        # In production: call GetYourGuide/Viator API
                        item.is_booked = True
                        item.booking_reference = ref
                        item.notes = (item.notes or '') + f'\nTicket: {ref}'
                        item.save()
                        cost = float(item.estimated_cost or 0)
                        total_booked_cost += cost
                        booking_results.append({
                            'item': item.title,
                            'type': 'attraction',
                            'status': 'ticket_purchased',
                            'reference': ref,
                            'cost': cost,
                        })

                    elif item.item_type == 'transport':
                        # Car rental or transport booking
                        item.is_booked = True
                        item.booking_reference = ref
                        item.notes = (item.notes or '') + f'\nBooked: {ref}'
                        item.save()
                        cost = float(item.estimated_cost or 0)
                        total_booked_cost += cost
                        booking_results.append({
                            'item': item.title,
                            'type': 'transport',
                            'status': 'booked',
                            'reference': ref,
                            'cost': cost,
                        })

                    else:
                        # Activities, notes — skip booking
                        booking_results.append({
                            'item': item.title,
                            'type': item.item_type,
                            'status': 'no_booking_needed',
                        })

                except Exception as e:
                    logger.error(f"Booking failed for item {item.id} ({item.title}): {e}")
                    errors.append({
                        'item': item.title,
                        'type': item.item_type,
                        'status': 'failed',
                        'error': str(e),
                    })

            # ── Step 2: Create a master Booking record ──
            from apps.bookings.models import Booking as BookingModel

            master_booking = BookingModel.objects.create(
                user=request.user,
                status='confirmed',
                total_amount=max(total_booked_cost, 0.01),
                currency=itinerary.currency,
                primary_traveler_name=request.user.get_full_name() or request.user.email,
                primary_traveler_email=request.user.email,
                primary_traveler_phone='',
                notes=f'Auto-booked from itinerary: {itinerary.title}',
            )

            # ── Step 3: Update itinerary status ──
            if errors:
                itinerary.status = 'approved'  # revert if partial failure
            else:
                itinerary.status = 'booked'
                itinerary.actual_spent = total_booked_cost

            itinerary.save(update_fields=['status', 'actual_spent', 'updated_at'])

            return Response({
                'success': len(errors) == 0,
                'status': itinerary.status,
                'booking_number': master_booking.booking_number,
                'total_cost': total_booked_cost,
                'items_booked': len([r for r in booking_results if r.get('status') not in ('no_booking_needed', 'already_booked')]),
                'items_skipped': len([r for r in booking_results if r.get('status') == 'no_booking_needed']),
                'items_failed': len(errors),
                'booking_results': booking_results,
                'errors': errors,
                'message': (
                    f'All items booked successfully! Booking #{master_booking.booking_number}'
                    if not errors else
                    f'{len(errors)} item(s) failed to book. Please retry.'
                ),
            })

        except Exception as e:
            logger.error(f"Booking agent error: {e}", exc_info=True)
            itinerary.status = 'approved'
            itinerary.save(update_fields=['status', 'updated_at'])
            return Response(
                {'error': f'Booking failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Generic status update with validation."""
        itinerary = self.get_object()
        new_status = request.data.get('status')

        valid_transitions = {
            'draft': ['planned', 'cancelled'],
            'planned': ['approved', 'draft', 'cancelled'],
            'approved': ['booking', 'draft', 'cancelled'],
            'booking': ['booked', 'approved'],
            'booked': ['active', 'cancelled'],
            'active': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': ['draft'],
        }

        allowed = valid_transitions.get(itinerary.status, [])
        if new_status not in allowed:
            return Response(
                {'error': f'Cannot transition from "{itinerary.status}" to "{new_status}". Allowed: {allowed}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        itinerary.status = new_status
        itinerary.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(itinerary)
        return Response({
            'success': True,
            'status': new_status,
            'itinerary': serializer.data,
        })


class ItineraryDayViewSet(viewsets.ModelViewSet):
    """ViewSet for ItineraryDay model."""
    queryset = ItineraryDay.objects.all()
    serializer_class = ItineraryDaySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['itinerary']
    ordering = ['day_number']

    def get_queryset(self):
        if self.request.user.is_staff:
            return ItineraryDay.objects.all()
        return ItineraryDay.objects.filter(itinerary__user=self.request.user)


class ItineraryItemViewSet(viewsets.ModelViewSet):
    """ViewSet for ItineraryItem model."""
    queryset = ItineraryItem.objects.all()
    serializer_class = ItineraryItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['day', 'item_type', 'is_booked']
    ordering = ['order', 'start_time']

    def get_queryset(self):
        if self.request.user.is_staff:
            return ItineraryItem.objects.all()
        return ItineraryItem.objects.filter(day__itinerary__user=self.request.user)


class WeatherViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Weather model."""
    queryset = Weather.objects.all()
    serializer_class = WeatherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['location', 'date']
    ordering = ['date']
