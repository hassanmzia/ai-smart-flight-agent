import logging
import urllib.parse

import requests
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserContact
from .serializers import UserContactSerializer

logger = logging.getLogger(__name__)

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'


def _geocode(city: str, country: str = '', address: str = '') -> tuple:
    """
    Geocode a city/address via Nominatim (free, no API key).
    Returns (lat, lng) or (None, None) on failure.
    """
    query = f"{address}, {city}" if address else city
    if country:
        query += f", {country}"
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={'q': query, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'AI-Travel-Planner/1.0'},
            timeout=5,
        )
        data = resp.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        logger.warning('Geocoding failed for %s: %s', query, e)
    return None, None


# ------------------------------------------------------------------ #
#  CRUD endpoints                                                      #
# ------------------------------------------------------------------ #

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def contact_list_create(request):
    """List all contacts or create a new one."""
    if request.method == 'GET':
        contacts = UserContact.objects.filter(owner=request.user)
        serializer = UserContactSerializer(contacts, many=True)
        return Response({'success': True, 'contacts': serializer.data})

    # POST — create
    serializer = UserContactSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    contact = serializer.save(owner=request.user)

    # Geocode in-band (fast enough for single saves)
    lat, lng = _geocode(contact.city, contact.country, contact.address)
    if lat is not None:
        contact.latitude = lat
        contact.longitude = lng
        contact.save(update_fields=['latitude', 'longitude'])

    return Response(
        {'success': True, 'contact': UserContactSerializer(contact).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def contact_detail(request, pk):
    """Retrieve, update, or delete a contact."""
    try:
        contact = UserContact.objects.get(pk=pk, owner=request.user)
    except UserContact.DoesNotExist:
        return Response(
            {'success': False, 'error': 'Contact not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        return Response({'success': True, 'contact': UserContactSerializer(contact).data})

    if request.method == 'DELETE':
        contact.delete()
        return Response({'success': True})

    # PUT — update
    serializer = UserContactSerializer(contact, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    contact = serializer.save()

    # Re-geocode if city or address changed
    changed = set(serializer.validated_data.keys())
    if changed & {'city', 'country', 'address'}:
        lat, lng = _geocode(contact.city, contact.country, contact.address)
        if lat is not None:
            contact.latitude = lat
            contact.longitude = lng
            contact.save(update_fields=['latitude', 'longitude'])

    return Response({'success': True, 'contact': UserContactSerializer(contact).data})


# ------------------------------------------------------------------ #
#  Near-destination filter                                             #
# ------------------------------------------------------------------ #

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contacts_near_destination(request):
    """
    Return the current user's contacts whose city matches (case-insensitive)
    or whose coordinates are within ~50 km of the destination.

    Query params:
        city  (required)  — destination city name
    """
    city = request.query_params.get('city', '').strip()
    if not city:
        return Response(
            {'success': False, 'error': 'city query param is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    contacts = UserContact.objects.filter(owner=request.user)

    # First pass: exact city match (case-insensitive)
    matched = list(contacts.filter(city__iexact=city))
    matched_ids = {c.id for c in matched}

    # Second pass: geocode destination, find contacts within ~50 km
    dest_lat, dest_lng = _geocode(city)
    if dest_lat is not None:
        for contact in contacts.exclude(id__in=matched_ids):
            if contact.latitude is not None and contact.longitude is not None:
                # Rough distance check (~1 degree ≈ 111 km)
                dlat = abs(contact.latitude - dest_lat)
                dlng = abs(contact.longitude - dest_lng)
                if dlat < 0.45 and dlng < 0.45:  # ~50 km box
                    matched.append(contact)

    serializer = UserContactSerializer(matched, many=True)
    return Response({
        'success': True,
        'contacts': serializer.data,
        'destination_lat': dest_lat,
        'destination_lng': dest_lng,
    })
