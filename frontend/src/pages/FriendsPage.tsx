import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useToast } from '@/hooks/useNotifications';
import socialService, { UserContact, ContactFormData } from '@/services/socialService';

// ------------------------------------------------------------------ //
//  Marker icons                                                       //
// ------------------------------------------------------------------ //

const RELATIONSHIP_EMOJI: Record<string, string> = {
  friend: '\u{1F9D1}\u200D\u{1F91D}\u200D\u{1F9D1}',  // friends
  family: '\u{1F3E0}',    // house
  colleague: '\u{1F4BC}', // briefcase
  other: '\u{1F4CD}',     // pin
};

function friendIcon(relationship: string) {
  const emoji = RELATIONSHIP_EMOJI[relationship] || '\u{1F4CD}';
  return L.divIcon({
    html: `<span style="font-size:28px;line-height:1">${emoji}</span>`,
    className: 'friend-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -28],
  });
}

const destinationIcon = L.divIcon({
  html: '<span style="font-size:32px;line-height:1">\u{1F3AF}</span>',
  className: 'dest-marker',
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -32],
});

// ------------------------------------------------------------------ //
//  Empty form state                                                   //
// ------------------------------------------------------------------ //

const BLANK_FORM: ContactFormData = {
  name: '',
  city: '',
  country: '',
  address: '',
  phone: '',
  email: '',
  relationship: 'friend',
  notes: '',
};

// ------------------------------------------------------------------ //
//  Component                                                          //
// ------------------------------------------------------------------ //

export default function FriendsPage() {
  const { showSuccess, showError } = useToast();

  // Contacts state
  const [contacts, setContacts] = useState<UserContact[]>([]);
  const [loading, setLoading] = useState(true);

  // Form state
  const [form, setForm] = useState<ContactFormData>({ ...BLANK_FORM });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  // Map / destination search
  const [destCity, setDestCity] = useState('');
  const [nearbyContacts, setNearbyContacts] = useState<UserContact[]>([]);
  const [destCoords, setDestCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [searching, setSearching] = useState(false);

  // ---- data fetch ------------------------------------------------ //

  const fetchContacts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await socialService.listContacts();
      setContacts(data);
    } catch {
      showError('Failed to load contacts');
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => { fetchContacts(); }, [fetchContacts]);

  // ---- form handlers --------------------------------------------- //

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim() || !form.city.trim()) {
      showError('Name and City are required');
      return;
    }
    setSaving(true);
    try {
      if (editingId) {
        await socialService.updateContact(editingId, form);
        showSuccess('Contact updated');
      } else {
        await socialService.createContact(form);
        showSuccess('Contact added');
      }
      setForm({ ...BLANK_FORM });
      setEditingId(null);
      fetchContacts();
    } catch {
      showError('Failed to save contact');
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (contact: UserContact) => {
    setEditingId(contact.id);
    setForm({
      name: contact.name,
      city: contact.city,
      country: contact.country,
      address: contact.address,
      phone: contact.phone,
      email: contact.email,
      relationship: contact.relationship,
      notes: contact.notes,
    });
    // scroll to form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id: number) => {
    try {
      await socialService.deleteContact(id);
      showSuccess('Contact removed');
      fetchContacts();
    } catch {
      showError('Failed to delete contact');
    }
  };

  const handleCancel = () => {
    setEditingId(null);
    setForm({ ...BLANK_FORM });
  };

  // ---- destination search ---------------------------------------- //

  const handleDestSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!destCity.trim()) return;
    setSearching(true);
    try {
      const data = await socialService.contactsNearDestination(destCity.trim());
      setNearbyContacts(data.contacts);
      if (data.destination_lat && data.destination_lng) {
        setDestCoords({ lat: data.destination_lat, lng: data.destination_lng });
      } else {
        setDestCoords(null);
      }
      if (data.contacts.length === 0) {
        showError(`No contacts found near ${destCity}`);
      }
    } catch {
      showError('Search failed');
    } finally {
      setSearching(false);
    }
  };

  // ---- derive map centre ---------------------------------------- //

  const mapPins = nearbyContacts.filter((c) => c.latitude && c.longitude);
  const mapCenter: [number, number] = destCoords
    ? [destCoords.lat, destCoords.lng]
    : mapPins.length > 0
      ? [mapPins[0].latitude!, mapPins[0].longitude!]
      : [40, -3]; // default world view

  // ---- render ---------------------------------------------------- //

  const inputCls =
    'w-full px-3 py-2 border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500';

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 max-w-7xl mx-auto space-y-8">
      {/* ------- Header ------- */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-4xl">{'\u{1F465}'}</span> Friends & Family
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Keep a personal address-book of friends and family. When planning a trip you can stay at their place instead of a hotel.
        </p>
      </div>

      {/* ------- Add / Edit form ------- */}
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {editingId ? 'Edit Contact' : 'Add a Contact'}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name *</label>
            <input name="name" value={form.name} onChange={handleChange} className={inputCls} placeholder="Uncle Ahmed" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City *</label>
            <input name="city" value={form.city} onChange={handleChange} className={inputCls} placeholder="Paris" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Country</label>
            <input name="country" value={form.country || ''} onChange={handleChange} className={inputCls} placeholder="France" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Address</label>
            <input name="address" value={form.address || ''} onChange={handleChange} className={inputCls} placeholder="45 Rue de Rivoli" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
            <input name="phone" value={form.phone || ''} onChange={handleChange} className={inputCls} placeholder="+33 6 12 34 56 78" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input name="email" type="email" value={form.email || ''} onChange={handleChange} className={inputCls} placeholder="ahmed@example.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Relationship</label>
            <select name="relationship" value={form.relationship} onChange={handleChange} className={inputCls}>
              <option value="friend">Friend</option>
              <option value="family">Family</option>
              <option value="colleague">Colleague</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
            <textarea name="notes" value={form.notes || ''} onChange={handleChange} rows={2} className={inputCls} placeholder="Has a guest room, near Metro line 1" />
          </div>
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={saving} className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50">
            {saving ? 'Saving...' : editingId ? 'Update Contact' : 'Add Contact'}
          </button>
          {editingId && (
            <button type="button" onClick={handleCancel} className="px-5 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 text-sm font-semibold rounded-lg transition-colors">
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* ------- Contacts list ------- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          My Contacts ({contacts.length})
        </h2>
        {loading ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading...</p>
        ) : contacts.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No contacts yet. Add your first friend or family member above.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {contacts.map((c) => (
              <div
                key={c.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{RELATIONSHIP_EMOJI[c.relationship] || '\u{1F4CD}'}</span>
                    <div>
                      <div className="font-semibold text-gray-900 dark:text-white">{c.name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {c.city}{c.country ? `, ${c.country}` : ''}
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                    {c.relationship}
                  </span>
                </div>

                {c.address && <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">{'\u{1F4CD}'} {c.address}</div>}
                {c.phone && <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{'\u{1F4DE}'} {c.phone}</div>}
                {c.email && <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{'\u{2709}\uFE0F'} {c.email}</div>}
                {c.notes && <div className="text-xs text-gray-600 dark:text-gray-300 mt-2 italic">{c.notes}</div>}

                <div className="flex gap-2 mt-3 pt-2 border-t border-gray-100 dark:border-gray-700">
                  <button onClick={() => handleEdit(c)} className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline">
                    Edit
                  </button>
                  <button onClick={() => handleDelete(c.id)} className="text-xs font-semibold text-red-500 dark:text-red-400 hover:underline">
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ------- Friends at Destination (map) ------- */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Friends Near a Destination
        </h2>
        <form onSubmit={handleDestSearch} className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination City</label>
            <input
              value={destCity}
              onChange={(e) => setDestCity(e.target.value)}
              className={inputCls}
              placeholder="e.g. Paris"
            />
          </div>
          <button type="submit" disabled={searching} className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 whitespace-nowrap">
            {searching ? 'Searching...' : 'Find Friends'}
          </button>
        </form>

        {/* Results */}
        {nearbyContacts.length > 0 && (
          <div className="text-sm text-gray-700 dark:text-gray-300">
            Found <strong>{nearbyContacts.length}</strong> contact{nearbyContacts.length > 1 ? 's' : ''} near <strong>{destCity}</strong>:
            {' '}
            {nearbyContacts.map((c) => c.name).join(', ')}
          </div>
        )}

        {/* Map */}
        {(mapPins.length > 0 || destCoords) && (
          <div className="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700" style={{ height: 420 }}>
            <MapContainer
              key={`${mapCenter[0]}-${mapCenter[1]}`}
              center={mapCenter}
              zoom={destCoords ? 12 : 4}
              scrollWheelZoom
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Destination pin */}
              {destCoords && (
                <Marker position={[destCoords.lat, destCoords.lng]} icon={destinationIcon}>
                  <Popup>
                    <strong>Destination:</strong> {destCity}
                  </Popup>
                </Marker>
              )}

              {/* Friend pins */}
              {mapPins.map((c) => (
                <Marker
                  key={c.id}
                  position={[c.latitude!, c.longitude!]}
                  icon={friendIcon(c.relationship)}
                >
                  <Popup>
                    <div className="text-sm">
                      <strong>{c.name}</strong>
                      <div className="text-gray-500">{c.city}{c.country ? `, ${c.country}` : ''}</div>
                      {c.address && <div>{c.address}</div>}
                      {c.phone && <div>{c.phone}</div>}
                      <div className="mt-1 italic text-xs">{c.relationship}</div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}
      </div>
    </div>
  );
}
