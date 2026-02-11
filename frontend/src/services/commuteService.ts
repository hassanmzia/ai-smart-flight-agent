import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

export interface TrafficCondition {
  current_condition: string;
  traffic_level: number;
  last_updated: string;
  description: string;
}

export interface PublicTransportOption {
  type: string;
  icon: string;
  availability: string;
  frequency: string;
  operating_hours: string;
  fare: string;
  coverage: string;
}

export interface PeakHour {
  start: string;
  end: string;
  severity: string;
}

export interface MajorRoute {
  name: string;
  description: string;
  current_condition: string;
  average_speed: string;
}

export interface TrafficIncident {
  type: string;
  icon: string;
  severity: string;
  location: string;
  description: string;
  reported: string;
  estimated_clearance: string;
}

export interface CommuteTime {
  public_transport: string;
  driving: string;
  taxi?: string;
}

export interface ParkingInfo {
  availability: string;
  average_cost_hourly: string;
  average_cost_daily: string;
  recommendations: string[];
}

export interface TrafficPattern {
  morning_rush: string;
  midday: string;
  evening_rush: string;
  typical_description: string;
}

export interface CommuteTip {
  icon: string;
  title: string;
  description: string;
}

export interface RoadConditions {
  overall: string;
  active_construction: number;
  major_closures: number;
  detour_info: string;
}

export interface CommuteData {
  success: boolean;
  location: string;
  traffic_conditions: TrafficCondition;
  public_transport: PublicTransportOption[];
  peak_hours: {
    morning: PeakHour;
    evening: PeakHour;
  };
  major_routes: MajorRoute[];
  current_incidents: TrafficIncident[];
  commute_times: {
    airport: CommuteTime;
    downtown_to_suburbs: CommuteTime;
    cross_city: CommuteTime;
  };
  parking_info: ParkingInfo;
  traffic_patterns: Record<string, TrafficPattern>;
  commute_tips: CommuteTip[];
  road_conditions: RoadConditions;
  error?: string;
}

export interface CommuteSearchParams {
  city: string;
}

class CommuteService {
  private apiUrl = `${API_BASE_URL}/api/commute`;

  async getCommuteInfo(params: CommuteSearchParams): Promise<CommuteData> {
    try {
      const response = await axios.get(`${this.apiUrl}/info/`, {
        params: {
          city: params.city,
        },
      });

      return response.data;
    } catch (error: any) {
      console.error('Error fetching commute information:', error);
      throw new Error(error.response?.data?.error || error.message || 'Failed to fetch commute information');
    }
  }
}

const commuteService = new CommuteService();
export default commuteService;
