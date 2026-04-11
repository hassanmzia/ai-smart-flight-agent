import json
import logging
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

from .models import Itinerary, ItineraryDay, ItineraryItem, Weather, TripFeedback
from .serializers import (
    ItinerarySerializer, ItineraryDaySerializer,
    ItineraryItemSerializer, WeatherSerializer, TripFeedbackSerializer
)
from .pdf_generator import ProfessionalPDFGenerator
from .email_service import EmailService, CalendarService
from .feedback_service import FeedbackAnalyzer


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


    # ── AI Trip Storytelling ──

    @action(detail=True, methods=['post'], url_path='generate-story')
    def generate_story(self, request, pk=None):
        """
        Generate a rich, immersive day-by-day travel narrative for the itinerary.

        Tries OpenAI (GPT) when OPENAI_API_KEY is configured; otherwise falls
        back to a deterministic template-based narrative engine.

        Returns a structured JSON story and saves the narrative text to the
        itinerary's ``ai_narrative`` field.
        """
        logger = logging.getLogger(__name__)
        itinerary = self.get_object()

        # Prefetch days and items
        days = itinerary.days.all().order_by('day_number')
        days_data = []
        for day in days:
            items = day.items.all().order_by('order', 'start_time')
            days_data.append({
                'day': day,
                'items': list(items),
            })

        # Try OpenAI first, fall back to template
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        story = None

        if api_key and api_key not in ('your_openai_api_key_here', ''):
            try:
                story = self._generate_story_openai(itinerary, days_data, api_key)
            except Exception as exc:
                logger.warning(
                    "OpenAI story generation failed, falling back to template: %s", exc
                )

        if story is None:
            story = self._generate_story_template(itinerary, days_data)

        # Persist a readable narrative to ai_narrative for PDF export
        narrative_lines = [f"# {story['title']}", ""]
        if story.get('summary'):
            narrative_lines += [story['summary'], ""]
        for day_story in story.get('days', []):
            date_str = f" ({day_story['date']})" if day_story.get('date') else ""
            narrative_lines.append(
                f"## Day {day_story['day_number']}: {day_story['title']}{date_str}"
            )
            narrative_lines.append("")
            narrative_lines.append(day_story.get('narrative', ''))
            narrative_lines.append("")
            if day_story.get('highlights'):
                narrative_lines.append("**Highlights:**")
                for hl in day_story['highlights']:
                    narrative_lines.append(f"- {hl}")
                narrative_lines.append("")

        itinerary.ai_narrative = "\n".join(narrative_lines)
        itinerary.save(update_fields=['ai_narrative', 'updated_at'])

        return Response({
            'success': True,
            'story': story,
            'message': 'Travel story generated successfully.',
        })

    # ── OpenAI story generation ──

    @staticmethod
    def _generate_story_openai(itinerary, days_data, api_key):
        """Call OpenAI to produce a structured travel narrative."""
        import openai

        # Build a concise itinerary summary for the prompt
        itinerary_summary_parts = []
        for entry in days_data:
            day = entry['day']
            date_str = day.date.strftime('%A, %B %d, %Y') if day.date else ''
            items_desc = []
            for item in entry['items']:
                time_str = item.start_time.strftime('%I:%M %p') if item.start_time else 'Flexible'
                cost_str = f" (${item.estimated_cost:.0f})" if item.estimated_cost else ""
                loc = item.location_name or ''
                items_desc.append(
                    f"  - {time_str}: [{item.item_type}] {item.title}"
                    f"{' at ' + loc if loc else ''}{cost_str}"
                )
            items_text = "\n".join(items_desc) if items_desc else "  (free day)"
            itinerary_summary_parts.append(
                f"Day {day.day_number} ({date_str}): {day.title or 'Untitled'}\n{items_text}"
            )

        itinerary_text = "\n\n".join(itinerary_summary_parts)

        system_prompt = (
            "You are a world-class travel writer. Given a trip itinerary, "
            "produce an immersive, evocative day-by-day travel narrative. "
            "Return ONLY valid JSON (no markdown fences) with this schema:\n"
            "{\n"
            '  "title": "string — a captivating story title",\n'
            '  "destination": "string",\n'
            '  "summary": "string — 2-3 sentence overview",\n'
            '  "days": [\n'
            "    {\n"
            '      "day_number": int,\n'
            '      "date": "string (e.g. Monday, June 5, 2025)",\n'
            '      "title": "string — evocative day title",\n'
            '      "narrative": "string — 3-5 paragraph immersive narrative",\n'
            '      "highlights": ["string", ...],\n'
            '      "mood": "string — one-word mood like adventurous, relaxed, cultural"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

        user_prompt = (
            f"Trip: {itinerary.title}\n"
            f"Destination: {itinerary.destination}\n"
            f"Dates: {itinerary.start_date} to {itinerary.end_date}\n"
            f"Travelers: {itinerary.number_of_travelers}\n\n"
            f"Itinerary:\n{itinerary_text}\n\n"
            "Write the travel story now."
        )

        client = openai.OpenAI(api_key=api_key, timeout=25.0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=4000,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        story = json.loads(raw)
        return story

    # ── Template-based fallback story generation ──

    @staticmethod
    def _generate_story_template(itinerary, days_data):
        """
        Produce a compelling template-based narrative without any AI API.

        Uses item types, times-of-day, and destination context to craft
        evocative prose.
        """

        def _time_of_day(t):
            """Return a descriptive time-of-day string from a time object."""
            if t is None:
                return "during the day"
            hour = t.hour
            if hour < 6:
                return "in the early pre-dawn hours"
            elif hour < 9:
                return "as the morning sun casts a golden glow"
            elif hour < 12:
                return "as the morning unfolds"
            elif hour < 14:
                return "around midday"
            elif hour < 17:
                return "in the warm afternoon"
            elif hour < 20:
                return "as the evening settles in"
            else:
                return "under the night sky"

        def _item_narrative(item, destination):
            """Create a narrative sentence for a single itinerary item."""
            name = item.title or "an unnamed stop"
            location = item.location_name or destination
            time_ctx = _time_of_day(item.start_time)
            item_type = (item.item_type or '').lower()

            templates = {
                'restaurant': (
                    f"{time_ctx.capitalize()}, you savor the local cuisine at "
                    f"{name}, letting the flavors of {location} dance on your palate."
                ),
                'hotel': (
                    f"{time_ctx.capitalize()}, you settle into the comfort of "
                    f"{name}, your home away from home in {location}."
                ),
                'flight': (
                    f"{time_ctx.capitalize()}, you board your flight — "
                    f"{name} — feeling the anticipation build as the journey begins."
                ),
                'attraction': (
                    f"{time_ctx.capitalize()}, you discover the wonders of "
                    f"{name}, immersing yourself in everything {location} has to offer."
                ),
                'activity': (
                    f"{time_ctx.capitalize()}, you dive into an unforgettable experience — "
                    f"{name} — creating memories that will last a lifetime."
                ),
                'transport': (
                    f"{time_ctx.capitalize()}, you hop aboard {name}, "
                    f"watching the scenery of {location} glide past your window."
                ),
                'note': (
                    f"{time_ctx.capitalize()}, a gentle reminder: {name}."
                ),
            }

            return templates.get(item_type, (
                f"{time_ctx.capitalize()}, you experience {name} in {location}, "
                f"adding another chapter to your adventure."
            ))

        destination = itinerary.destination
        num_days = len(days_data)
        total_items = sum(len(e['items']) for e in days_data)

        # Determine overall mood hints
        mood_options = [
            'adventurous', 'cultural', 'relaxed', 'vibrant',
            'romantic', 'exploratory', 'festive', 'serene',
        ]

        summary = (
            f"Embark on a {num_days}-day journey through the heart of {destination}. "
            f"With {total_items} carefully curated experiences awaiting you, "
            f"this trip promises a tapestry of unforgettable moments — "
            f"from hidden local gems to iconic landmarks that define this extraordinary destination."
        )

        story_days = []
        for idx, entry in enumerate(days_data):
            day = entry['day']
            items = entry['items']
            day_num = day.day_number
            date_str = day.date.strftime('%A, %B %d, %Y') if day.date else ''

            # Pick a mood for the day based on item types present
            item_types = {item.item_type for item in items if item.item_type}
            if 'attraction' in item_types:
                mood = 'cultural'
            elif 'restaurant' in item_types and len(item_types) <= 2:
                mood = 'relaxed'
            elif 'activity' in item_types:
                mood = 'adventurous'
            elif 'flight' in item_types or 'transport' in item_types:
                mood = 'exploratory'
            else:
                mood = mood_options[idx % len(mood_options)]

            # Day title
            if idx == 0:
                day_title = day.title or f"Arrival in {destination}"
            elif idx == num_days - 1:
                day_title = day.title or f"Farewell to {destination}"
            else:
                day_title = day.title or f"Exploring {destination} — Day {day_num}"

            # Build the narrative paragraphs
            paragraphs = []

            # Opening paragraph
            if idx == 0:
                paragraphs.append(
                    f"Your adventure begins as you arrive in {destination}. "
                    f"The air is alive with new scents, sounds, and the promise of discovery. "
                    f"Today sets the stage for everything that lies ahead."
                )
            elif idx == num_days - 1:
                paragraphs.append(
                    f"The final day dawns in {destination}, bittersweet and beautiful. "
                    f"Every moment feels precious as you prepare to carry these memories home."
                )
            else:
                paragraphs.append(
                    f"Day {day_num} greets you with fresh possibilities in {destination}. "
                    f"The rhythm of the city beckons, and there is so much still to explore."
                )

            # Item narratives grouped into a paragraph
            if items:
                item_sentences = [
                    _item_narrative(item, destination) for item in items
                ]
                paragraphs.append(" ".join(item_sentences))
            else:
                paragraphs.append(
                    f"Today is yours to wander freely through {destination}, "
                    f"following your curiosity wherever it leads — perhaps a quiet "
                    f"cafe, a hidden garden, or a conversation with a friendly local."
                )

            # Closing paragraph for the day
            if items:
                cost_items = [item for item in items if item.estimated_cost]
                if cost_items:
                    total_day_cost = sum(float(c.estimated_cost) for c in cost_items)
                    paragraphs.append(
                        f"As the day winds down, you reflect on the experiences "
                        f"that made it special — an estimated ${total_day_cost:.0f} "
                        f"well invested in memories that money cannot truly measure."
                    )
                else:
                    paragraphs.append(
                        f"As the day comes to a close, you feel a deep sense of "
                        f"gratitude for the moments that made it unforgettable."
                    )

            narrative = "\n\n".join(paragraphs)

            # Highlights
            highlights = []
            for item in items[:5]:
                if item.item_type == 'restaurant':
                    highlights.append(f"Dining at {item.title}")
                elif item.item_type == 'attraction':
                    highlights.append(f"Visiting {item.title}")
                elif item.item_type == 'activity':
                    highlights.append(f"Experiencing {item.title}")
                elif item.item_type == 'flight':
                    highlights.append(f"Flight: {item.title}")
                elif item.item_type == 'hotel':
                    highlights.append(f"Staying at {item.title}")
                else:
                    highlights.append(item.title)

            story_days.append({
                'day_number': day_num,
                'date': date_str,
                'title': day_title,
                'narrative': narrative,
                'highlights': highlights,
                'mood': mood,
            })

        story = {
            'title': f"A Journey Through {destination}: {num_days} Days of Wonder",
            'destination': destination,
            'summary': summary,
            'days': story_days,
        }

        return story

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

    # Item types that require actual booking (flights, hotels, car rentals).
    # Attractions are booked only when they have a cost (ticketed venues).
    BOOKABLE_TYPES = {'flight', 'hotel', 'transport'}

    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        """
        ReAct Booking Agent — takes an approved itinerary and books essentials.

        Only books items that genuinely require a reservation:
        - Flights (airline tickets)
        - Hotels (accommodation)
        - Transport / car rentals
        - Attractions with a ticket cost (museums, theme parks, events)

        Restaurants, free activities, notes, and casual sightseeing are
        skipped — they don't need advance booking.

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

                # Determine if this item needs booking.
                # Attractions are only booked when they have a ticket cost
                # (e.g. museum entry, theme park, event). Free sightseeing
                # spots don't need advance booking.
                needs_booking = (
                    item.item_type in self.BOOKABLE_TYPES
                    or (item.item_type == 'attraction' and item.estimated_cost and float(item.estimated_cost) > 0)
                )

                if not needs_booking:
                    booking_results.append({
                        'item': item.title,
                        'type': item.item_type,
                        'status': 'no_booking_needed',
                    })
                    continue

                # Generate booking reference
                ref = f"BK-{item.item_type[:3].upper()}-{_uuid.uuid4().hex[:8].upper()}"

                # Simulate booking based on item type
                try:
                    if item.item_type == 'flight':
                        # In production: call Amadeus/Skyscanner booking API
                        label = 'Booked'
                        book_status = 'booked'
                    elif item.item_type == 'hotel':
                        # In production: call Booking.com/Hotels.com API
                        label = 'Booked'
                        book_status = 'booked'
                    elif item.item_type == 'transport':
                        # In production: car rental / transfer booking API
                        label = 'Booked'
                        book_status = 'booked'
                    elif item.item_type == 'attraction':
                        # In production: call GetYourGuide/Viator API
                        label = 'Ticket'
                        book_status = 'ticket_purchased'
                    else:
                        label = 'Booked'
                        book_status = 'booked'

                    item.is_booked = True
                    item.booking_reference = ref
                    item.notes = (item.notes or '') + f'\n{label}: {ref}'
                    item.save()
                    cost = float(item.estimated_cost or 0)
                    total_booked_cost += cost
                    booking_results.append({
                        'item': item.title,
                        'type': item.item_type,
                        'status': book_status,
                        'reference': ref,
                        'cost': cost,
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

    @action(detail=True, methods=['post'], url_path='geocode-items')
    def geocode_items(self, request, pk=None):
        """
        Geocode itinerary items that are missing coordinates.

        Uses the MapsClient (Google Maps) if a MAPS_API_KEY is configured.
        Falls back to a lightweight Nominatim (OpenStreetMap) lookup otherwise.
        Items that already have lat/lng are skipped.

        Returns the count of items updated and the refreshed itinerary.
        """
        import logging as _logging
        import time as _time
        _logger = _logging.getLogger(__name__)

        itinerary = self.get_object()
        # Find items needing geocoding: those with location_name OR title
        all_items = list(ItineraryItem.objects.filter(
            day__itinerary=itinerary,
            latitude__isnull=True,
        ))
        items_missing = [
            item for item in all_items
            if (item.location_name and item.location_name.strip())
            or (item.title and item.title.strip())
        ]

        updated = 0
        errors = []

        geocode_count = 0
        for item in items_missing:
            raw = (item.location_name or item.title).strip()
            query = self._clean_geocode_query(raw)
            if not query:
                _logger.info(f"Skipping non-location: '{item.title}'")
                continue
            if item.location_address:
                query = f"{query}, {item.location_address}"
            elif itinerary.destination:
                query = f"{query}, {itinerary.destination}"
            _logger.info(f"Geocoding '{item.title}' -> query='{query}'")

            # Respect Nominatim rate limit: 1 req/sec
            if geocode_count > 0:
                _time.sleep(1.2)
            geocode_count += 1

            coords = self._geocode_query(query, _logger)
            if coords:
                item.latitude = coords[0]
                item.longitude = coords[1]
                update_fields = ['latitude', 'longitude', 'updated_at']
                # Backfill location_name from title if it was empty
                if not item.location_name and item.title:
                    item.location_name = item.title
                    update_fields.append('location_name')
                item.save(update_fields=update_fields)
                updated += 1
                _logger.info(f"Geocoded '{item.title}' -> ({coords[0]}, {coords[1]})")
            else:
                errors.append(item.title)
                _logger.warning(f"Geocode failed for '{item.title}' (query='{query}')")

        serializer = self.get_serializer(itinerary)
        return Response({
            'success': True,
            'items_geocoded': updated,
            'items_failed': errors,
            'itinerary': serializer.data,
        })

    @staticmethod
    def _clean_geocode_query(raw: str) -> str:
        """Extract a meaningful place name from a descriptive title."""
        import re
        q = raw.strip().rstrip('.')

        # 1. Strip cost annotations: (~$15/person), ($20), ~$30, (~free, estimated 2 hours)
        q = re.sub(r'\(?\~?\$[\d,.]+[^)]*\)?', '', q).strip()
        q = re.sub(r'\([^)]*\)', '', q).strip()

        # 2. Strip pipe separators: "Texas Flame | Best Steakhouse" → "Texas Flame"
        q = q.split('|')[0].strip()

        # 3. Take text before first descriptive comma/clause
        parts = re.split(
            r',\s+(?:an?\s|offering|enjoying|featuring|where|with|located|which|this|the\s|learning|known|overlooking|serving|celebrating|honoring)',
            q, maxsplit=1, flags=re.IGNORECASE,
        )
        q = parts[0].strip()

        # 4. Strip trailing "for its/for the/for a" clauses
        q = re.split(r'\s+for\s+(?:its|the|a|an|your|some)\s', q, maxsplit=1, flags=re.IGNORECASE)[0].strip()

        # 5. Extract place name after preposition: "Lunch at Naked Farmer" → "Naked Farmer"
        m = re.search(
            r'\b(?:at|to|into|toward)\s+(?:the\s+)?(?!your\b|a\s+|an\s+|relax|rest|sleep|pack|freshen)(.+)',
            q, re.IGNORECASE,
        )
        if m:
            q = m.group(1).strip()

        # 6. Strip leading action verbs
        q = re.sub(
            r'^(?:Visit|Attend|Explore|Enjoy|Head|Return|Go|Walk|Drive|Take|Spend|Have|Grab|Check\s*out|Check\s*in)\s+(?:to\s+)?(?:the\s+)?',
            '', q, flags=re.IGNORECASE,
        ).strip()

        # 7. Strip trailing filler
        q = re.split(
            r'\s+(?:again\b|to\s+relax|to\s+freshen|to\s+see|to\s+learn|to\s+enjoy)',
            q, maxsplit=1, flags=re.IGNORECASE,
        )[0].strip()

        # 8. Skip vague non-location phrases
        skip = {'hotel', 'your hotel', 'the hotel', 'relax', 'rest',
                'freshen up', 'pack', 'sleep', 'airport', 'the airport'}
        if q.lower() in skip or len(q) < 3:
            return ''

        return q

    @staticmethod
    def _geocode_query(query: str, logger) -> tuple | None:
        """Try Google Maps first, fall back to Nominatim."""
        import requests as _requests
        import time as _time

        # Try Google Maps client if key is available
        try:
            from apps.agents.integrations.maps_client import MapsClient
            client = MapsClient()
            if client.api_key:
                result = client.geocode(query)
                if result:
                    return (result['latitude'], result['longitude'])
        except Exception as e:
            logger.debug(f"Google Maps geocode failed: {e}")

        # Fallback: Nominatim (OpenStreetMap) — free, no key needed
        for attempt in range(2):
            try:
                resp = _requests.get(
                    'https://nominatim.openstreetmap.org/search',
                    params={'q': query, 'format': 'json', 'limit': 1},
                    headers={'User-Agent': 'AITravelAgent/1.0'},
                    timeout=10,
                )
                if resp.status_code == 429:
                    logger.warning(f"Nominatim rate-limited for '{query}', retrying...")
                    _time.sleep(2)
                    continue
                if resp.ok and resp.json():
                    data = resp.json()[0]
                    return (float(data['lat']), float(data['lon']))
                logger.warning(f"Nominatim empty result for '{query}' (status={resp.status_code})")
                break
            except Exception as e:
                logger.warning(f"Nominatim geocode failed for '{query}': {e}")
                if attempt == 0:
                    _time.sleep(1)

        return None

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
            # Signal frontend to show feedback modal when trip is completed
            'feedback_requested': new_status == 'completed',
        })

    @action(detail=True, methods=['get', 'post'], url_path='feedback')
    def feedback(self, request, pk=None):
        """
        GET: Retrieve feedback for an itinerary.
        POST: Submit post-trip feedback with NLP analysis.

        POST body:
        - overall_rating: 1-5 (required)
        - flight_rating, hotel_rating, activities_rating, food_rating,
          value_for_money_rating: 1-5 (optional)
        - loved_most, would_change, additional_comments: text (optional)
        - would_visit_again, would_recommend: boolean (optional)
        - tags: list of strings (optional)
        """
        itinerary = self.get_object()

        if request.method == 'GET':
            try:
                fb = itinerary.feedback
                return Response(TripFeedbackSerializer(fb).data)
            except TripFeedback.DoesNotExist:
                return Response(
                    {'error': 'No feedback submitted yet.'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # POST — submit feedback
        # Check if feedback already exists
        if TripFeedback.objects.filter(itinerary=itinerary).exists():
            return Response(
                {'error': 'Feedback already submitted for this trip.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TripFeedbackSerializer(data={
            **request.data,
            'itinerary': itinerary.id,
            'user': request.user.id,
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        feedback = serializer.save(user=request.user, itinerary=itinerary)

        # Run NLP analysis on the feedback text
        try:
            nlp_results = FeedbackAnalyzer.analyze(feedback)
            feedback.sentiment = nlp_results.get('sentiment', '')
            feedback.sentiment_score = nlp_results.get('sentiment_score')
            feedback.emotions = nlp_results.get('emotions', {})
            feedback.is_toxic = nlp_results.get('is_toxic', False)
            feedback.toxicity_score = nlp_results.get('toxicity_score')
            feedback.extracted_topics = nlp_results.get('extracted_topics', [])
            feedback.learned_preferences = nlp_results.get('learned_preferences', {})
            feedback.save()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"NLP analysis failed: {e}")

        return Response({
            'success': True,
            'message': 'Thank you for your feedback!',
            'feedback': TripFeedbackSerializer(feedback).data,
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
