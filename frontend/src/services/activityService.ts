import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface ActivityPlace {
  name: string;
  description: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
  rating: number;
  reviews: number;
  website: string;
  phone: string;
  thumbnail: string;
  icon: string;
  hours: string;
}

export interface ActivitySearchResponse {
  success: boolean;
  results: ActivityPlace[];
  total: number;
  city: string;
  interest: string;
  interest_label: string;
  icon: string;
  source: string;
  city_lat: number | null;
  city_lng: number | null;
  error?: string;
}

export interface RoadTripWaypoint {
  name: string;
  icon: string;
  description: string;
  latitude: number;
  longitude: number;
  stop_number: number;
  distance_fraction: number;
}

export interface RoadTripResponse {
  success: boolean;
  from_city: string;
  to_city: string;
  from_lat: number;
  from_lng: number;
  to_lat: number;
  to_lng: number;
  waypoints: RoadTripWaypoint[];
  total_stops: number;
  error?: string;
}

export const INTEREST_CATEGORIES = [
  { key: 'birding', label: 'Birding', icon: '🐦' },
  { key: 'hiking', label: 'Hiking', icon: '🥾' },
  { key: 'boating', label: 'Boating', icon: '⛵' },
  { key: 'camping', label: 'Camping', icon: '⛺' },
  { key: 'picnic', label: 'Picnic', icon: '🧺' },
  { key: 'fishing', label: 'Fishing', icon: '🎣' },
  { key: 'golfing', label: 'Golfing', icon: '⛳' },
  { key: 'scouting', label: 'Scouting', icon: '🏕️' },
  { key: 'cross_country', label: 'Cross-Country Drive', icon: '🚗' },
  { key: 'student_travel', label: 'Student Travel', icon: '🎓' },
] as const;

class ActivityService {
  private apiUrl = `${API_BASE_URL}/api/activities`;

  async searchActivities(city: string, interest: string): Promise<ActivitySearchResponse> {
    const response = await axios.get(`${this.apiUrl}/search/`, {
      params: { city, interest },
    });
    return response.data;
  }

  async roadTripWaypoints(fromCity: string, toCity: string, stops?: number): Promise<RoadTripResponse> {
    const response = await axios.get(`${this.apiUrl}/road-trip/`, {
      params: { from_city: fromCity, to_city: toCity, stops },
    });
    return response.data;
  }
}

const activityService = new ActivityService();
export default activityService;
