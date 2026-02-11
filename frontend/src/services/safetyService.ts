import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface SafetyAlert {
  type: string;
  severity: string;
  icon: string;
  title: string;
  message: string;
  issued_at: string;
}

export interface EmergencyContacts {
  police: string;
  ambulance: string;
  fire: string;
  tourist_police: string;
  embassy: string;
}

export interface SafetyTip {
  icon: string;
  title: string;
  description: string;
}

export interface TransportationSafety {
  public_transport: {
    rating: string;
    tips: string[];
  };
  walking: {
    rating: string;
    tips: string[];
  };
}

export interface HealthInfo {
  tap_water: string;
  vaccinations_required: string[];
  hospitals: string;
  pharmacies: string;
  air_quality: string;
}

export interface LocalLaw {
  icon: string;
  title: string;
  description: string;
}

export interface TravelAdvisory {
  level: string;
  last_updated: string;
  summary: string;
}

export interface SafetyData {
  success: boolean;
  location: string;
  overall_rating: string;
  safety_score: number;
  active_alerts: SafetyAlert[];
  emergency_contacts: EmergencyContacts;
  safety_tips: SafetyTip[];
  areas_to_avoid: string[];
  safe_areas: string[];
  transportation_safety: TransportationSafety;
  health_info: HealthInfo;
  local_laws: LocalLaw[];
  travel_advisory: TravelAdvisory;
  error?: string;
}

export interface SafetySearchParams {
  city: string;
  start_date?: string;
  end_date?: string;
}

class SafetyService {
  private apiUrl = `${API_BASE_URL}/api/safety`;

  async getSafetyInfo(params: SafetySearchParams): Promise<SafetyData> {
    try {
      const response = await axios.get(`${this.apiUrl}/info/`, {
        params: {
          city: params.city,
          start_date: params.start_date,
          end_date: params.end_date,
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Error fetching safety information:', error);
      throw new Error(error.response?.data?.error || error.message || 'Failed to fetch safety information');
    }
  }
}

const safetyService = new SafetyService();
export default safetyService;
