"""
Enhanced Price Monitoring Service
Monitors flight and hotel prices, sends real-time WebSocket alerts on price drops.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


class PriceMonitorService:
    """Service for monitoring and alerting on price changes."""

    @staticmethod
    def check_price_watches():
        """Check all active price watches and send alerts for price drops."""
        from .models import PriceWatch
        from apps.notifications.tasks import send_notification

        channel_layer = get_channel_layer()
        watches = PriceWatch.objects.filter(is_active=True).select_related('user')

        alerts_sent = 0
        for watch in watches:
            try:
                new_price = PriceMonitorService._fetch_current_price(watch)
                if new_price is None:
                    continue

                old_price = watch.current_price
                watch.current_price = new_price
                watch.last_checked = timezone.now()

                # Update price history
                history = watch.price_history or []
                history.append({
                    'date': timezone.now().isoformat(),
                    'price': float(new_price)
                })
                # Keep last 90 days of history
                if len(history) > 180:
                    history = history[-180:]
                watch.price_history = history

                # Update lowest price
                if watch.lowest_price is None or new_price < watch.lowest_price:
                    watch.lowest_price = new_price

                watch.save()

                # Check if we should alert
                should_alert = False
                alert_message = ""

                if watch.target_price and new_price <= watch.target_price:
                    should_alert = True
                    alert_message = (
                        f"Price dropped to ${new_price}! Below your target of "
                        f"${watch.target_price}. Book now before it goes back up!"
                    )
                elif watch.notify_on_any_drop and old_price and new_price < old_price:
                    drop_amount = old_price - new_price
                    drop_pct = (drop_amount / old_price * 100)
                    if drop_pct >= 3:  # Only alert on 3%+ drops
                        should_alert = True
                        recommendation = (
                            "Book now — this is a great deal!"
                            if drop_pct >= 10
                            else "Consider booking soon — prices may rise again."
                        )
                        alert_message = (
                            f"Price dropped ${drop_amount:.0f} ({drop_pct:.0f}%) "
                            f"from ${old_price} to ${new_price}! {recommendation}"
                        )

                if should_alert:
                    # Send WebSocket real-time alert
                    try:
                        async_to_sync(channel_layer.group_send)(
                            f'user_{watch.user.id}',
                            {
                                'type': 'notification_message',
                                'notification': {
                                    'type': 'price_alert',
                                    'title': f'{"Flight" if watch.watch_type == "flight" else "Hotel"} Price Drop!',
                                    'message': alert_message,
                                    'data': {
                                        'watch_id': watch.id,
                                        'watch_type': watch.watch_type,
                                        'current_price': float(new_price),
                                        'previous_price': float(old_price) if old_price else None,
                                        'target_price': float(watch.target_price) if watch.target_price else None,
                                        'search_params': watch.search_params,
                                    }
                                }
                            }
                        )
                    except Exception as e:
                        logger.warning(f"WebSocket alert failed: {e}")

                    # Also send persistent notification
                    send_notification.delay(
                        user_id=watch.user.id,
                        notification_type='price_drop',
                        title=f'{"Flight" if watch.watch_type == "flight" else "Hotel"} Price Drop!',
                        message=alert_message,
                        data={
                            'watch_id': watch.id,
                            'watch_type': watch.watch_type,
                            'current_price': float(new_price),
                            'search_params': watch.search_params,
                        },
                        channels=['database', 'websocket', 'email']
                    )
                    alerts_sent += 1

            except Exception as e:
                logger.error(f"Error checking price watch {watch.id}: {e}")
                continue

        return alerts_sent

    @staticmethod
    def _fetch_current_price(watch):
        """Fetch the current price for a watch item."""
        try:
            if watch.watch_type == 'flight':
                from .agent_tools import FlightSearchTool
                params = watch.search_params
                results = FlightSearchTool.search_flights(
                    origin=params.get('origin', ''),
                    destination=params.get('destination', ''),
                    date=params.get('date', ''),
                    return_date=params.get('return_date'),
                    passengers=params.get('passengers', 1),
                )
                if results and results.get('best_flights'):
                    prices = []
                    for flight in results['best_flights'][:5]:
                        price = flight.get('price')
                        if price:
                            # Extract numeric price
                            price_str = str(price).replace('$', '').replace(',', '')
                            try:
                                prices.append(Decimal(price_str))
                            except Exception:
                                pass
                    if prices:
                        return min(prices)

            elif watch.watch_type == 'hotel':
                from .agent_tools import HotelSearchTool
                params = watch.search_params
                results = HotelSearchTool.search_hotels(
                    location=params.get('location', ''),
                    check_in=params.get('check_in', ''),
                    check_out=params.get('check_out', ''),
                    guests=params.get('guests', 1),
                )
                if results and results.get('properties'):
                    prices = []
                    for hotel in results['properties'][:5]:
                        rate = hotel.get('rate_per_night', {})
                        price = rate.get('lowest') or rate.get('extracted_lowest')
                        if price:
                            price_str = str(price).replace('$', '').replace(',', '')
                            try:
                                prices.append(Decimal(price_str))
                            except Exception:
                                pass
                    if prices:
                        return min(prices)

        except Exception as e:
            logger.error(f"Error fetching price for watch {watch.id}: {e}")

        return None

    @staticmethod
    def create_watch(user, watch_type, search_params, target_price=None):
        """Create a new price watch."""
        from .models import PriceWatch

        watch = PriceWatch.objects.create(
            user=user,
            watch_type=watch_type,
            search_params=search_params,
            target_price=Decimal(str(target_price)) if target_price else None,
            is_active=True,
        )

        # Fetch initial price
        initial_price = PriceMonitorService._fetch_current_price(watch)
        if initial_price:
            watch.current_price = initial_price
            watch.lowest_price = initial_price
            watch.price_history = [{'date': timezone.now().isoformat(), 'price': float(initial_price)}]
            watch.last_checked = timezone.now()
            watch.save()

        return watch
