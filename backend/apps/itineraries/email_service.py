"""
Email Service for Travel Itineraries
Supports SMTP, SendGrid, and AWS SES
"""

import os
import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Optional: SendGrid support
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

# Optional: AWS SES support
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_SES_AVAILABLE = True
except ImportError:
    AWS_SES_AVAILABLE = False


class EmailService:
    """
    Unified email service supporting multiple backends:
    - Django SMTP (default)
    - SMTP (app2.py compatible)
    - SendGrid
    - AWS SES
    """

    @staticmethod
    def send_itinerary_email_django(
        to_email: str,
        subject: str,
        itinerary_text: str,
        pdf_path: Optional[str] = None,
        user_name: Optional[str] = None,
        destination: Optional[str] = None,
        dates: Optional[str] = None,
        ics_path: Optional[str] = None
    ) -> bool:
        """
        Send itinerary email using Django's email backend.

        Args:
            to_email: Recipient email address
            subject: Email subject
            itinerary_text: Full itinerary text (for email body)
            pdf_path: Path to PDF attachment
            user_name: User's name for personalization
            destination: Trip destination
            dates: Trip dates
            ics_path: Optional calendar file (.ics) path

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Render HTML email template
            context = {
                'user_name': user_name or 'Traveler',
                'destination': destination or 'Your Destination',
                'dates': dates or 'TBD',
                'itinerary_text': itinerary_text,
                'year': datetime.now().year
            }

            html_content = render_to_string('emails/itinerary_email.html', context)
            text_content = strip_tags(html_content)

            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")

            # Attach PDF
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    email.attach(
                        filename=Path(pdf_path).name,
                        content=f.read(),
                        mimetype='application/pdf'
                    )

            # Attach calendar file
            if ics_path and Path(ics_path).exists():
                with open(ics_path, 'rb') as f:
                    email.attach(
                        filename='itinerary.ics',
                        content=f.read(),
                        mimetype='text/calendar'
                    )

            email.send()
            return True

        except Exception as e:
            print(f"Django email send failed: {str(e)}")
            return False

    @staticmethod
    def send_itinerary_email_smtp(
        to_email: str,
        subject: str,
        pdf_path: str,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send itinerary email via SMTP (app2.py compatible).

        Args:
            to_email: Recipient email
            subject: Email subject
            pdf_path: Path to PDF file
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_pass: SMTP password
            html_body: Optional HTML email body

        Returns:
            True if sent successfully, False otherwise
        """
        # Get SMTP config from env or parameters
        host = smtp_host or os.getenv("SMTP_HOST", "")
        port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        user = smtp_user or os.getenv("SMTP_USER", "")
        password = smtp_pass or os.getenv("SMTP_PASS", "")

        if not (host and user and password):
            raise RuntimeError(
                "SMTP not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS."
            )

        if not pdf_path or not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found at: {pdf_path}")

        try:
            msg = EmailMessage()
            msg["From"] = user
            msg["To"] = to_email
            msg["Subject"] = subject

            # Set email body
            if html_body:
                msg.add_alternative(html_body, subtype='html')
            else:
                msg.set_content("Your travel itinerary is attached to this email.")

            # Attach PDF
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            msg.add_attachment(
                pdf_bytes,
                maintype="application",
                subtype="pdf",
                filename=Path(pdf_path).name
            )

            # Send via SMTP
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"SMTP email send failed: {str(e)}")
            return False

    @staticmethod
    def send_itinerary_email_sendgrid(
        to_email: str,
        subject: str,
        html_content: str,
        pdf_path: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Send itinerary email via SendGrid.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            pdf_path: Optional PDF attachment path
            api_key: SendGrid API key

        Returns:
            True if sent successfully, False otherwise
        """
        if not SENDGRID_AVAILABLE:
            raise RuntimeError("SendGrid library not installed. Run: pip install sendgrid")

        api_key = api_key or os.getenv("SENDGRID_API_KEY")
        if not api_key:
            raise RuntimeError("SendGrid API key not configured")

        try:
            from_email = os.getenv("SENDGRID_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)

            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            # Attach PDF
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                    encoded_pdf = base64.b64encode(pdf_data).decode()

                attachment = Attachment(
                    FileContent(encoded_pdf),
                    FileName(Path(pdf_path).name),
                    FileType('application/pdf'),
                    Disposition('attachment')
                )
                message.attachment = attachment

            sg = SendGridAPIClient(api_key)
            response = sg.send(message)

            return response.status_code in [200, 201, 202]

        except Exception as e:
            print(f"SendGrid email send failed: {str(e)}")
            return False

    @staticmethod
    def send_itinerary_email_ses(
        to_email: str,
        subject: str,
        html_content: str,
        pdf_path: Optional[str] = None,
        region: str = "us-east-1"
    ) -> bool:
        """
        Send itinerary email via AWS SES.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            pdf_path: Optional PDF attachment path
            region: AWS region

        Returns:
            True if sent successfully, False otherwise
        """
        if not AWS_SES_AVAILABLE:
            raise RuntimeError("Boto3 library not installed. Run: pip install boto3")

        try:
            from_email = os.getenv("AWS_SES_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)

            # Create multipart message
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email

            # Add HTML body
            msg_body = MIMEMultipart('alternative')
            html_part = MIMEText(html_content.encode('utf-8'), 'html', 'utf-8')
            msg_body.attach(html_part)
            msg.attach(msg_body)

            # Attach PDF
            if pdf_path and Path(pdf_path).exists():
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()

                pdf_part = MIMEApplication(pdf_data)
                pdf_part.add_header('Content-Disposition', 'attachment', filename=Path(pdf_path).name)
                msg.attach(pdf_part)

            # Send via SES
            ses_client = boto3.client('ses', region_name=region)
            response = ses_client.send_raw_email(
                Source=from_email,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )

            return True

        except ClientError as e:
            print(f"AWS SES email send failed: {str(e)}")
            return False
        except Exception as e:
            print(f"Email send failed: {str(e)}")
            return False

    @classmethod
    def send_itinerary_email(
        cls,
        to_email: str,
        subject: str,
        itinerary_text: str,
        pdf_path: Optional[str] = None,
        user_name: Optional[str] = None,
        destination: Optional[str] = None,
        dates: Optional[str] = None,
        backend: str = "auto"
    ) -> bool:
        """
        Send itinerary email using best available backend.

        Args:
            to_email: Recipient email
            subject: Email subject
            itinerary_text: Itinerary text
            pdf_path: PDF attachment path
            user_name: User name for personalization
            destination: Trip destination
            dates: Trip dates
            backend: Email backend ("auto", "django", "smtp", "sendgrid", "ses")

        Returns:
            True if sent successfully, False otherwise
        """
        # Auto-select backend
        if backend == "auto":
            if hasattr(settings, 'EMAIL_BACKEND') and settings.EMAIL_BACKEND:
                backend = "django"
            elif os.getenv("SENDGRID_API_KEY") and SENDGRID_AVAILABLE:
                backend = "sendgrid"
            elif os.getenv("SMTP_HOST"):
                backend = "smtp"
            else:
                backend = "django"

        # Send via selected backend
        if backend == "django":
            return cls.send_itinerary_email_django(
                to_email, subject, itinerary_text, pdf_path,
                user_name, destination, dates
            )
        elif backend == "smtp":
            return cls.send_itinerary_email_smtp(
                to_email, subject, pdf_path
            )
        elif backend == "sendgrid":
            html_content = f"<html><body><h1>{destination or 'Your Trip'}</h1><p>Please find your itinerary attached.</p></body></html>"
            return cls.send_itinerary_email_sendgrid(
                to_email, subject, html_content, pdf_path
            )
        elif backend == "ses":
            html_content = f"<html><body><h1>{destination or 'Your Trip'}</h1><p>Please find your itinerary attached.</p></body></html>"
            return cls.send_itinerary_email_ses(
                to_email, subject, html_content, pdf_path
            )
        else:
            raise ValueError(f"Unknown email backend: {backend}")


class CalendarService:
    """Generate .ics calendar files for itineraries"""

    @staticmethod
    def create_ics_file(
        destination: str,
        start_date: str,
        end_date: str,
        activities: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """
        Create .ics calendar file with itinerary events.

        Args:
            destination: Trip destination
            start_date: Trip start date (YYYY-MM-DD)
            end_date: Trip end date (YYYY-MM-DD)
            activities: List of activities with 'title', 'time', 'description'
            output_path: Path to save .ics file

        Returns:
            Path to generated .ics file
        """
        try:
            from icalendar import Calendar, Event as ICalEvent
            from datetime import datetime

            cal = Calendar()
            cal.add('prodid', '-//AI Smart Flight Agent//Trip Planner//EN')
            cal.add('version', '2.0')
            cal.add('calscale', 'GREGORIAN')
            cal.add('method', 'PUBLISH')
            cal.add('x-wr-calname', f'{destination} Trip')
            cal.add('x-wr-timezone', 'UTC')

            for activity in activities:
                event = ICalEvent()
                event.add('summary', activity.get('title', 'Activity'))
                event.add('description', activity.get('description', ''))

                # Parse datetime
                activity_time = activity.get('time')
                if activity_time:
                    event.add('dtstart', activity_time)
                    event.add('dtend', activity_time + timedelta(hours=1))

                event.add('location', destination)
                event.add('status', 'CONFIRMED')

                cal.add_component(event)

            # Write to file
            with open(output_path, 'wb') as f:
                f.write(cal.to_ical())

            return output_path

        except ImportError:
            print("icalendar library not installed. Run: pip install icalendar")
            return ""
        except Exception as e:
            print(f"Calendar generation failed: {str(e)}")
            return ""
