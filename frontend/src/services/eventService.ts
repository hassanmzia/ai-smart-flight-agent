import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface Event {
  name: string;
  category: string;
  icon: string;
  start_date: string;
  end_date: string;
  is_multi_day: boolean;
  duration_days: number;
  venue: string;
  description: string;
  price_range: string;
  ticket_price: number;
  expected_attendance: number;
  organizer: string;
  website: string;
  tags: string[];
  rating: number;
  review_count: number;
}

export interface EventSearchParams {
  city: string;
  start_date?: string;
  end_date?: string;
  category?: string;
}

export interface EventSearchResponse {
  success: boolean;
  results: Event[];
  total: number;
  location: string;
  start_date: string;
  end_date: string;
  error?: string;
}

class EventService {
  private apiUrl = `${API_BASE_URL}/api/events`;

  async searchEvents(params: EventSearchParams): Promise<EventSearchResponse> {
    try {
      const response = await axios.get(`${this.apiUrl}/search/`, {
        params: {
          city: params.city,
          start_date: params.start_date,
          end_date: params.end_date,
          category: params.category,
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Error searching events:', error);
      throw new Error(error.response?.data?.error || error.message || 'Failed to search events');
    }
  }
}

const eventService = new EventService();
export default eventService;
