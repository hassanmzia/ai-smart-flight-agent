import api from './api';

export interface UserContact {
  id: number;
  name: string;
  city: string;
  country: string;
  address: string;
  phone: string;
  email: string;
  relationship: 'friend' | 'family' | 'colleague' | 'other';
  notes: string;
  latitude: number | null;
  longitude: number | null;
  invite_status: 'none' | 'invited' | 'accepted';
  invite_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactFormData {
  name: string;
  city: string;
  country?: string;
  address?: string;
  phone?: string;
  email?: string;
  relationship?: string;
  notes?: string;
}

const socialService = {
  async listContacts(): Promise<UserContact[]> {
    const res = await api.get('/api/social/contacts/');
    return res.data.contacts;
  },

  async createContact(data: ContactFormData): Promise<UserContact> {
    const res = await api.post('/api/social/contacts/', data);
    return res.data.contact;
  },

  async updateContact(id: number, data: Partial<ContactFormData>): Promise<UserContact> {
    const res = await api.put(`/api/social/contacts/${id}/`, data);
    return res.data.contact;
  },

  async deleteContact(id: number): Promise<void> {
    await api.delete(`/api/social/contacts/${id}/`);
  },

  async contactsNearDestination(city: string): Promise<{
    contacts: UserContact[];
    destination_lat: number | null;
    destination_lng: number | null;
  }> {
    const res = await api.get('/api/social/contacts/near-destination/', {
      params: { city },
    });
    return res.data;
  },
};

export default socialService;
