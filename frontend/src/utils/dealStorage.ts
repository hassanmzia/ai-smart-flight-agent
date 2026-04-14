/**
 * Lightweight client-side storage for the user's "saved" / "wallet" deals.
 *
 * We deliberately keep this out of the backend for now — it's purely a UX
 * convenience (let the traveller bookmark a coupon they'll use later). If we
 * ever need cross-device sync we can swap the implementation here without
 * touching DealsPage.
 */
import type { Deal } from '@/services/dealsService';

const KEY = 'savedDealsV1';

const readRaw = (): Record<string, Deal> => {
  try {
    const json = localStorage.getItem(KEY);
    if (!json) return {};
    const parsed = JSON.parse(json);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
};

const writeRaw = (data: Record<string, Deal>): void => {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
  } catch {
    /* ignore quota errors */
  }
};

/** Return all saved deals as a list (most recently saved first). */
export const getSavedDeals = (): Deal[] => {
  const obj = readRaw();
  // Insertion order preserved by JSON.parse for string keys; reverse so newest
  // saves are shown first.
  return Object.values(obj).reverse();
};

export const isDealSaved = (dealId: number): boolean => {
  return String(dealId) in readRaw();
};

export const saveDeal = (deal: Deal): void => {
  const obj = readRaw();
  // Deleting then re-inserting moves the key to the end so getSavedDeals()
  // (which reverses) lists the most recent save first.
  delete obj[String(deal.id)];
  obj[String(deal.id)] = deal;
  writeRaw(obj);
};

export const removeSavedDeal = (dealId: number): void => {
  const obj = readRaw();
  delete obj[String(dealId)];
  writeRaw(obj);
};

export const toggleSavedDeal = (deal: Deal): boolean => {
  if (isDealSaved(deal.id)) {
    removeSavedDeal(deal.id);
    return false;
  }
  saveDeal(deal);
  return true;
};

export const clearSavedDeals = (): void => {
  writeRaw({});
};

/** Lightweight cross-component change notification (no Zustand needed). */
export const SAVED_DEALS_EVENT = 'savedDealsChanged';
export const notifySavedDealsChanged = () => {
  try {
    window.dispatchEvent(new Event(SAVED_DEALS_EVENT));
  } catch {
    /* SSR / jsdom — no-op */
  }
};
