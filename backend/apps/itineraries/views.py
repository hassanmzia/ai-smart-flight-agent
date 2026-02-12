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
        """Generate markdown-formatted itinerary text from database model"""
        lines = []

        # Title and metadata
        lines.append(f"# {itinerary.title or itinerary.destination}")
        lines.append(f"\n**Destination:** {itinerary.destination}")
        lines.append(f"**Dates:** {itinerary.start_date} to {itinerary.end_date}")
        lines.append(f"**Budget:** ${itinerary.estimated_budget or 0}")
        lines.append("")

        # Add itinerary overview if available
        if itinerary.description:
            lines.append("## Overview")
            lines.append(itinerary.description)
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

                if item.location_name:
                    lines.append(f"  📍 {item.location_name}")

                if item.estimated_cost:
                    lines.append(f"  💰 ${item.estimated_cost}")

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
