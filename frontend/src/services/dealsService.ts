import api from './api';
import { API_ENDPOINTS } from '@/utils/constants';

/**
 * Coupon shape returned by ``GET /api/agents/coupons``.
 *
 * The backend returns two slightly different shapes depending on whether the
 * coupon is from a real partner row or one of the demo coupons.  This type
 * accepts either via optional fields; ``getDealsList`` below normalises them
 * into a single canonical ``Deal`` so the UI doesn't have to think about it.
 */
export interface RawCoupon {
  id: number;
  code: string;
  title: string;
  description?: string;
  discount_type: 'percentage' | 'fixed' | 'bogo' | 'freebie' | string;
  discount_value: number;
  min_spend?: number;
  valid_until?: string | null;
  terms?: string;
  qr_data?: string;
  // Demo-coupon flat fields:
  partner_name?: string;
  partner_category?: string;
  partner_destination?: string;
  // DB-coupon nested partner:
  partner?: {
    id?: number;
    name?: string;
    category?: string;
    destination?: string;
    rating?: number;
  };
}

/**
 * Canonical, flat shape used by every component on the Deals page.
 */
export interface Deal {
  id: number;
  code: string;
  title: string;
  description: string;
  discountType: 'percentage' | 'fixed' | 'bogo' | 'freebie' | string;
  discountValue: number;
  minSpend: number;
  validUntil: string | null;
  terms: string;
  qrData: string;
  partnerName: string;
  partnerCategory: string;
  partnerDestination: string;
  partnerRating: number | null;
}

const normalize = (raw: RawCoupon): Deal => {
  const partnerName = raw.partner_name || raw.partner?.name || 'Partner';
  const partnerCategory =
    raw.partner_category || raw.partner?.category || 'other';
  const partnerDestination =
    raw.partner_destination || raw.partner?.destination || '';
  const partnerRating =
    typeof raw.partner?.rating === 'number' ? raw.partner.rating : null;

  // Build a sensible default qr_data payload if the backend didn't send one.
  // We encode JSON the user can scan with any QR app to get the code +
  // partner context for redemption at the counter.
  const qrData =
    raw.qr_data ||
    JSON.stringify({
      code: raw.code,
      partner: partnerName,
      title: raw.title,
    });

  return {
    id: raw.id,
    code: raw.code,
    title: raw.title || raw.code,
    description: raw.description || '',
    discountType: raw.discount_type || 'percentage',
    discountValue: Number(raw.discount_value || 0),
    minSpend: Number(raw.min_spend || 0),
    validUntil: raw.valid_until || null,
    terms: raw.terms || '',
    qrData,
    partnerName,
    partnerCategory,
    partnerDestination,
    partnerRating,
  };
};

/**
 * Fetch the active deals/coupons list, optionally filtering by destination
 * and/or category. Always returns a plain array; the call never throws — on
 * error we return an empty list so the UI can render its "no deals" state.
 */
export const getDealsList = async (
  filter: { destination?: string; category?: string } = {},
): Promise<Deal[]> => {
  try {
    const params: Record<string, string> = {};
    if (filter.destination) params.destination = filter.destination;
    if (filter.category) params.category = filter.category;
    const res = await api.get(API_ENDPOINTS.AGENT.COUPONS, { params });
    const data = res.data;
    const list: RawCoupon[] = Array.isArray(data)
      ? data
      : Array.isArray(data?.coupons)
      ? data.coupons
      : Array.isArray(data?.items)
      ? data.items
      : Array.isArray(data?.results)
      ? data.results
      : [];
    return list.map(normalize);
  } catch (err) {
    // Soft-fail so the page shows an empty state instead of crashing.
    return [];
  }
};

/**
 * Redeem a coupon code (recorded server-side for tracking).
 *
 * NOTE: most physical-redemption coupons are also fine to "use" without
 * calling this endpoint — the user can simply present the code/QR at the
 * counter. We expose this so we can mark a coupon as used in the user's
 * Travel Wallet history.
 */
export const redeemDeal = async (
  code: string,
  orderTotal: number = 0,
): Promise<{
  success: boolean;
  discount?: number;
  message?: string;
}> => {
  try {
    const res = await api.post(API_ENDPOINTS.AGENT.COUPONS_REDEEM, {
      coupon_code: code,
      order_total: orderTotal,
    });
    return res.data || { success: false };
  } catch (err: any) {
    return {
      success: false,
      message:
        err?.response?.data?.error || err?.message || 'Could not redeem',
    };
  }
};

/**
 * Format the discount as a short headline (e.g. "20% OFF", "$15 OFF",
 * "BOGO", "FREE"). Used on coupon cards and the print/PDF view.
 */
export const formatDiscount = (deal: Pick<Deal, 'discountType' | 'discountValue'>) => {
  switch (deal.discountType) {
    case 'percentage':
      return `${deal.discountValue}% OFF`;
    case 'fixed':
      return `$${deal.discountValue} OFF`;
    case 'bogo':
      return 'BUY 1 GET 1';
    case 'freebie':
      return 'FREE';
    default:
      return `${deal.discountValue}`;
  }
};

/**
 * Days remaining until a coupon expires (or null if it has no expiry).
 * Negative values mean the coupon is already expired.
 */
export const daysUntilExpiry = (validUntil: string | null): number | null => {
  if (!validUntil) return null;
  try {
    const expiry = new Date(validUntil).getTime();
    const now = Date.now();
    return Math.ceil((expiry - now) / (1000 * 60 * 60 * 24));
  } catch {
    return null;
  }
};
