/**
 * Shared helpers for turning a `/api/agents/plan` response into a fully
 * persisted Itinerary (with day-by-day items for flights, hotels, restaurants,
 * attractions, etc.).
 *
 * Used by both the AI Travel Planner page and the Collaborative Trip Planner
 * page so that "Create Shared Trip" produces the same rich itinerary as the
 * single-user planner.
 */

import api from '@/services/api';
import {
  createItinerary,
  createItineraryDay,
  createItineraryItem,
} from '@/services/itineraryService';
import type { Itinerary } from '@/types';

export type ItemType =
  | 'flight'
  | 'hotel'
  | 'restaurant'
  | 'attraction'
  | 'activity'
  | 'transport'
  | 'note';

export interface ParsedActivity {
  time: string | undefined;
  title: string;
  itemType: ItemType;
  estimatedCost: number | undefined;
  url?: string;
}

/**
 * Pull the first http(s) URL out of a chunk of markdown — either from a
 * `[text](url)` link or a bare URL. Returns the URL (without surrounding
 * punctuation) or undefined.
 */
function extractUrl(text: string): string | undefined {
  const mdMatch = text.match(/\[[^\]]+\]\((https?:\/\/[^\s)]+)\)/);
  if (mdMatch) return mdMatch[1];
  const bareMatch = text.match(/(https?:\/\/[^\s)<>]+)/);
  if (bareMatch) return bareMatch[1].replace(/[.,;:!?]+$/, '');
  return undefined;
}

/**
 * Strip markdown link syntax (`[text](url)`) down to just the `text`, and
 * remove bare URLs, so the resulting string reads cleanly as an activity
 * title.
 */
function stripMarkdownLinks(text: string): string {
  return text
    .replace(/\[([^\]]+)\]\((?:https?:\/\/[^\s)]+)\)/g, '$1')
    .replace(/\((?:https?:\/\/[^\s)]+)\)/g, '')
    .replace(/https?:\/\/[^\s)<>]+/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

export interface ParsedDay {
  dayNumber: number;
  title: string;
  activities: ParsedActivity[];
}

/* ─── Parsers ────────────────────────────────────────────────────────────── */

export function guessItemType(text: string): ItemType {
  const lower = text.toLowerCase();
  if (/\b(flight|fly|airport|depart|land|board)\b/.test(lower)) return 'flight';
  if (/\b(check.?in|check.?out|hotel|hostel|airbnb|accommodation|lodge|resort)\b/.test(lower))
    return 'hotel';
  if (/\b(breakfast|lunch|dinner|brunch|restaurant|cafe|eat|dine|dining|food|meal|cuisine)\b/.test(lower))
    return 'restaurant';
  if (/\b(museum|monument|palace|cathedral|tower|temple|castle|gallery|park|garden|landmark|visit|tour|sightsee|explore|attraction)\b/.test(lower))
    return 'attraction';
  if (/\b(taxi|uber|metro|subway|bus|train|tram|drive|car|transfer|commute|ride|transit)\b/.test(lower))
    return 'transport';
  return 'activity';
}

/** Extract a place name from a descriptive activity title. */
export function extractPlaceName(title: string): string {
  let q = title.replace(/\.\s*$/, '').trim();
  q = q.replace(/\(?\~?\$[\d,.]+[^)]*\)?/g, '').trim();
  q = q.replace(/\([^)]*\)/g, '').trim();
  q = q.split(/,\s+(?:an?\s|offering|enjoying|featuring|where|with|for|located|which|this)/i)[0].trim();
  const m = q.match(/\b(?:at|to|into)\s+(?:the\s+)?(?!your\b|a\s|an\s)(.+)/i);
  if (m) q = m[1].trim();
  q = q.replace(
    /^(?:Visit|Attend|Explore|Enjoy|Head|Return|Go|Walk|Drive|Take|Spend|Have|Grab)\s+(?:to\s+)?(?:the\s+)?/i,
    '',
  ).trim();
  q = q.split(/\s+(?:again\b|to\s+relax|to\s+freshen|for\s+a\s|for\s+the\s)/i)[0].trim();
  return q.length >= 3 ? q : title;
}

export function parseItineraryNarrative(text: string): ParsedDay[] {
  if (!text) return [];
  const days: ParsedDay[] = [];
  const dayPattern = /^##\s*Day\s+(\d+)\s*[:\-–]\s*(.*)$/gm;
  const matches: { index: number; dayNum: number; title: string }[] = [];
  let match;
  while ((match = dayPattern.exec(text)) !== null) {
    matches.push({ index: match.index, dayNum: parseInt(match[1]), title: match[2].trim() });
  }
  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].index;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    const section = text.slice(start, end);
    const activities: ParsedActivity[] = [];
    const timePattern = /\*{0,2}(\d{1,2}:\d{2}\s*[AaPp][Mm]?)\*{0,2}\s*[-–:]\s*(.+)/g;
    let timeMatch;
    while ((timeMatch = timePattern.exec(section)) !== null) {
      const timeStr = timeMatch[1].trim();
      const rawText = timeMatch[2].trim().replace(/\*\*/g, '').replace(/\*/g, '');
      const url = extractUrl(rawText);
      const activityText = stripMarkdownLinks(rawText);
      let cost: number | undefined;
      const costMatch = activityText.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) cost = parseFloat(costMatch[1]);
      activities.push({
        time: timeStr,
        title: activityText,
        itemType: guessItemType(activityText),
        estimatedCost: cost,
        url,
      });
    }
    const bulletPattern = /^[-*•]\s+(?!\d{1,2}:\d{2})(.+)/gm;
    let bulletMatch;
    while ((bulletMatch = bulletPattern.exec(section)) !== null) {
      const rawText = bulletMatch[1].trim().replace(/\*\*/g, '').replace(/\*/g, '');
      const bText = stripMarkdownLinks(rawText);
      if (activities.some((a) => bText.includes(a.title.slice(0, 20)))) continue;
      if (bText.startsWith('#') || bText.startsWith('---')) continue;
      const url = extractUrl(rawText);
      let cost: number | undefined;
      const costMatch = bText.match(/[\(~]*\$(\d+(?:\.\d+)?)\)?/);
      if (costMatch) cost = parseFloat(costMatch[1]);
      activities.push({
        time: undefined,
        title: bText,
        itemType: guessItemType(bText),
        estimatedCost: cost,
        url,
      });
    }
    days.push({ dayNumber: matches[i].dayNum, title: matches[i].title, activities });
  }
  return days;
}

/* ─── Save flow ──────────────────────────────────────────────────────────── */

export interface AiPlanInput {
  /** Free-form NL query e.g. "Plan a trip from NYC to Tokyo" */
  query?: string;
  origin_city: string;
  origin_country?: string;
  destination_city: string;
  destination_country?: string;
  departure_date: string;
  return_date?: string;
  passengers: number;
  budget?: number | string;
  cuisine?: string;
  travel_style?: string;
  interests?: string;
  accommodation_preference?: string;
}

export interface SaveAiItineraryOptions {
  /** Override the generated title. */
  titleOverride?: string;
  /** Mark the itinerary as shared and pre-attach collaborators. */
  isShared?: boolean;
  sharedWith?: string[];
  /** Override status, defaults to "planned". */
  status?: string;
}

/**
 * Call the AI Travel Planner backend (`/api/agents/plan`) and return its
 * full JSON response. Throws on transport / non-success responses.
 */
export async function generateAiPlan(input: AiPlanInput): Promise<any> {
  const originLabel = input.origin_country
    ? `${input.origin_city}, ${input.origin_country}`
    : input.origin_city;
  const destinationLabel = input.destination_country
    ? `${input.destination_city}, ${input.destination_country}`
    : input.destination_city;
  const response = await api.post(
    '/api/agents/plan',
    {
      query: input.query || `Plan a trip from ${originLabel} to ${destinationLabel}`,
      origin_city: input.origin_city,
      origin_country: input.origin_country || undefined,
      destination_city: input.destination_city,
      destination_country: input.destination_country || undefined,
      departure_date: input.departure_date,
      return_date: input.return_date || undefined,
      passengers: Number(input.passengers),
      budget: input.budget ? Number(input.budget) : undefined,
      cuisine: input.cuisine || undefined,
      travel_style: input.travel_style || undefined,
      interests: input.interests || undefined,
      accommodation_preference: input.accommodation_preference || undefined,
    },
    { timeout: 300000 },
  );
  const data = response.data;
  if (!data?.success) {
    throw new Error(data?.error || 'AI planning failed');
  }
  return data;
}

/**
 * Persist a `/api/agents/plan` response as a full Itinerary with day-by-day
 * items (flights, hotels, restaurants, attractions, etc.).
 *
 * Returns the created Itinerary record. The detail page (`/itineraries/:id`)
 * renders Flights / Hotels / Cars / Dining tabs by filtering the persisted
 * items on `item_type`, so once this returns the rich tabbed UI just works.
 */
export async function saveAiPlanAsItinerary(
  planResult: any,
  input: AiPlanInput,
  options: SaveAiItineraryOptions = {},
): Promise<Itinerary> {
  const start = input.departure_date;
  const end = input.return_date || input.departure_date;
  const originLabel = input.origin_country
    ? `${input.origin_city}, ${input.origin_country}`
    : input.origin_city;
  const destinationLabel = input.destination_country
    ? `${input.destination_city}, ${input.destination_country}`
    : input.destination_city;

  const rec = planResult?.recommendation;
  const totalCost = rec?.total_estimated_cost;
  const parsedDays = parseItineraryNarrative(planResult?.itinerary_text || '');

  const startD = new Date(start);
  const endD = new Date(end);
  const totalDays = Math.max(
    1,
    Math.ceil((endD.getTime() - startD.getTime()) / (1000 * 60 * 60 * 24)) + 1,
  );

  const itinerary = await createItinerary({
    title:
      options.titleOverride || `AI Trip: ${originLabel} to ${destinationLabel}`,
    destination: destinationLabel,
    origin_city: input.origin_city,
    origin_country: input.origin_country || '',
    destination_city: input.destination_city,
    destination_country: input.destination_country || '',
    start_date: start,
    end_date: end,
    status: options.status || 'planned',
    number_of_travelers: input.passengers,
    estimated_budget: totalCost
      ? String(totalCost)
      : input.budget
      ? String(input.budget)
      : undefined,
    currency: 'USD',
    description: `AI-planned trip from ${originLabel} to ${destinationLabel}. ${input.passengers} passenger(s).`,
    ai_narrative: planResult?.itinerary_text || '',
    is_shared: options.isShared || undefined,
    shared_with: options.sharedWith && options.sharedWith.length > 0
      ? options.sharedWith
      : undefined,
  });

  const itineraryId = Number(itinerary.id);

  for (let d = 1; d <= totalDays; d++) {
    const dayDate = new Date(startD);
    dayDate.setDate(dayDate.getDate() + d - 1);
    const dateStr = dayDate.toISOString().split('T')[0];
    const parsedDay = parsedDays.find((p) => p.dayNumber === d);
    const isFirstDay = d === 1;
    const isLastDay = d === totalDays;
    const dayTitle =
      parsedDay?.title ||
      (isFirstDay
        ? `Arrival in ${destinationLabel}`
        : isLastDay
        ? 'Departure Day'
        : `Explore ${destinationLabel}`);

    const day = await createItineraryDay({
      itinerary: itineraryId,
      day_number: d,
      date: dateStr,
      title: dayTitle,
    });
    const dayId = day.id!;
    let itemOrder = 0;

    if (isFirstDay) {
      if (rec?.recommended_flight) {
        const flight = rec.recommended_flight;
        const flightUrl =
          flight.bookingUrl ||
          flight.booking_url ||
          flight.link ||
          undefined;
        await createItineraryItem({
          day: dayId,
          item_type: 'flight',
          order: itemOrder++,
          title: `${flight.airline || 'Flight'} ${flight.flight_number || ''} - ${flight.departure_airport_code || originLabel} to ${flight.arrival_airport_code || destinationLabel}`,
          description: `${flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop(s)`}${flight.duration ? ` · ${Math.floor(flight.duration / 60)}h ${flight.duration % 60}m` : ''}`,
          start_time: flight.departure_time?.split(' ')[1]?.slice(0, 5) || undefined,
          estimated_cost: flight.price || undefined,
          location_name: flight.departure_airport || originLabel,
          url: flightUrl,
        });
      }
      if (rec?.recommended_hotel) {
        const hotel = rec.recommended_hotel;
        const hotelUrl =
          hotel.booking_url ||
          hotel.link ||
          hotel.website_url ||
          undefined;
        await createItineraryItem({
          day: dayId,
          item_type: 'hotel',
          order: itemOrder++,
          title: `Check in: ${hotel.name || hotel.hotel_name}`,
          description: `${hotel.stars || hotel.star_rating || 0} stars`,
          start_time: '15:00',
          estimated_cost: hotel.price || hotel.price_per_night || undefined,
          location_name: hotel.address || destinationLabel,
          url: hotelUrl,
        });
      }
    }

    if (isLastDay && totalDays > 1) {
      if (rec?.recommended_hotel) {
        const hotel = rec.recommended_hotel;
        const hotelUrl =
          hotel.booking_url ||
          hotel.link ||
          hotel.website_url ||
          undefined;
        await createItineraryItem({
          day: dayId,
          item_type: 'hotel',
          order: itemOrder++,
          title: `Check out: ${hotel.name || hotel.hotel_name}`,
          start_time: '10:00',
          location_name: hotel.address || destinationLabel,
          url: hotelUrl,
        });
      }
    }

    if (parsedDay && parsedDay.activities.length > 0) {
      for (const activity of parsedDay.activities) {
        const lowerTitle = activity.title.toLowerCase();
        if (isFirstDay && activity.itemType === 'flight' && itemOrder > 0) continue;
        if (
          isFirstDay &&
          lowerTitle.includes('check') &&
          lowerTitle.includes('in') &&
          activity.itemType === 'hotel'
        )
          continue;
        if (
          isLastDay &&
          lowerTitle.includes('check') &&
          lowerTitle.includes('out') &&
          activity.itemType === 'hotel'
        )
          continue;
        let timeHHMM: string | undefined;
        if (activity.time) {
          const tMatch = activity.time.match(/(\d{1,2}):(\d{2})\s*([AaPp][Mm]?)/);
          if (tMatch) {
            let hour = parseInt(tMatch[1]);
            const min = tMatch[2];
            const ampm = tMatch[3].toUpperCase();
            if (ampm.startsWith('P') && hour !== 12) hour += 12;
            if (ampm.startsWith('A') && hour === 12) hour = 0;
            timeHHMM = `${hour.toString().padStart(2, '0')}:${min}`;
          }
        }
        await createItineraryItem({
          day: dayId,
          item_type: activity.itemType,
          order: itemOrder++,
          title: activity.title,
          start_time: timeHHMM,
          estimated_cost: activity.estimatedCost,
          location_name: extractPlaceName(activity.title),
          url: activity.url,
        });
      }
    } else if (!isFirstDay && !isLastDay) {
      await createItineraryItem({
        day: dayId,
        item_type: 'activity',
        order: 0,
        title: `Explore ${destinationLabel}`,
        description: 'Add your planned activities for this day',
      });
    }
  }

  return itinerary;
}

/**
 * One-shot helper: generate the AI plan and persist it as an Itinerary in
 * a single call. Convenient for flows like "Create Shared Trip" where the
 * intermediate planning UI isn't shown to the user.
 */
export async function generateAndSaveAiItinerary(
  input: AiPlanInput,
  options: SaveAiItineraryOptions = {},
): Promise<{ itinerary: Itinerary; planResult: any }> {
  const planResult = await generateAiPlan(input);
  const itinerary = await saveAiPlanAsItinerary(planResult, input, options);
  return { itinerary, planResult };
}
