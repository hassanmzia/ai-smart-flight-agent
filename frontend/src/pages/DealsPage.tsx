import { useEffect, useMemo, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import {
  HeartIcon,
  ArrowDownTrayIcon,
  PrinterIcon,
  ClipboardIcon,
  XMarkIcon,
  MapPinIcon,
  TagIcon,
  ClockIcon,
  StarIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolid } from '@heroicons/react/24/solid';
import {
  getDealsList,
  formatDiscount,
  daysUntilExpiry,
  redeemDeal,
  type Deal,
} from '@/services/dealsService';
import {
  getSavedDeals,
  isDealSaved,
  toggleSavedDeal,
  removeSavedDeal,
  notifySavedDealsChanged,
  SAVED_DEALS_EVENT,
} from '@/utils/dealStorage';
import { printDealsAsWallet } from '@/utils/dealPrint';
import { getItineraries } from '@/services/itineraryService';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/utils/constants';

type ViewMode = 'all' | 'saved';
type SortMode = 'expiring' | 'discount' | 'newest';

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories', icon: '🏷️' },
  { value: 'hotel', label: 'Hotels', icon: '🏨' },
  { value: 'restaurant', label: 'Restaurants', icon: '🍽️' },
  { value: 'attraction', label: 'Attractions', icon: '🎟️' },
  { value: 'tour', label: 'Tours', icon: '🗺️' },
  { value: 'transport', label: 'Transport', icon: '🚗' },
  { value: 'shopping', label: 'Shopping', icon: '🛍️' },
  { value: 'spa', label: 'Spa & Wellness', icon: '💆' },
];

const CATEGORY_ICON: Record<string, string> = CATEGORY_OPTIONS.reduce(
  (acc, c) => ({ ...acc, [c.value]: c.icon }),
  {},
);

const qrSrc = (data: string, size = 200) =>
  `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(data)}`;

// ─────────────────────────────────────────────────────────────────────────
// DealCard — single coupon tile
// ─────────────────────────────────────────────────────────────────────────

interface DealCardProps {
  deal: Deal;
  saved: boolean;
  onToggleSave: (deal: Deal) => void;
  onCopyCode: (code: string) => void;
  onShowQr: (deal: Deal) => void;
}

const DealCard = ({
  deal,
  saved,
  onToggleSave,
  onCopyCode,
  onShowQr,
}: DealCardProps) => {
  const days = daysUntilExpiry(deal.validUntil);
  const isExpired = days !== null && days < 0;
  const expiringSoon = days !== null && days >= 0 && days <= 7;

  return (
    <div
      className={`relative bg-white dark:bg-gray-800 rounded-2xl border overflow-hidden shadow-sm hover:shadow-xl transition-all duration-200 group ${
        isExpired
          ? 'border-rose-200 dark:border-rose-900/50 opacity-70'
          : 'border-gray-200/80 dark:border-gray-700/60'
      }`}
    >
      {/* Discount strip */}
      <div
        className={`relative px-5 py-4 flex items-center justify-between ${
          isExpired
            ? 'bg-gradient-to-r from-rose-400 to-rose-500'
            : 'bg-gradient-to-r from-teal-500 via-emerald-500 to-cyan-500'
        }`}
      >
        <div>
          <div className="text-white font-extrabold text-2xl leading-none drop-shadow">
            {formatDiscount(deal)}
          </div>
          <div className="text-white/85 text-[11px] uppercase tracking-wider mt-1 flex items-center gap-1">
            <span>{CATEGORY_ICON[deal.partnerCategory] || '🏷️'}</span>
            <span>{deal.partnerCategory}</span>
          </div>
        </div>
        <button
          onClick={() => onToggleSave(deal)}
          aria-label={saved ? 'Remove from wallet' : 'Save to wallet'}
          className="p-2 rounded-full bg-white/15 hover:bg-white/25 backdrop-blur-sm text-white transition-colors"
        >
          {saved ? (
            <HeartSolid className="w-5 h-5 text-rose-300" />
          ) : (
            <HeartIcon className="w-5 h-5" />
          )}
        </button>

        {/* Decorative scallop */}
        <div className="absolute -bottom-2 left-0 right-0 h-2 flex justify-around">
          {Array.from({ length: 24 }).map((_, i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-white dark:bg-gray-800"
            />
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="p-5">
        <h3 className="font-bold text-gray-900 dark:text-white text-base leading-snug">
          {deal.title}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1.5">
          <MapPinIcon className="w-3.5 h-3.5" />
          <span className="truncate">
            {deal.partnerName}
            {deal.partnerDestination ? ` · ${deal.partnerDestination}` : ''}
          </span>
          {deal.partnerRating !== null && deal.partnerRating > 0 && (
            <span className="flex items-center gap-0.5 text-amber-500 ml-auto pl-2">
              <StarIcon className="w-3.5 h-3.5 fill-current" />
              {deal.partnerRating.toFixed(1)}
            </span>
          )}
        </p>

        {deal.description && (
          <p className="text-sm text-gray-600 dark:text-gray-300 mt-3 line-clamp-2">
            {deal.description}
          </p>
        )}

        {/* Mini-meta row */}
        <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-gray-500 dark:text-gray-400">
          {deal.minSpend > 0 && (
            <span>Min. spend ${deal.minSpend.toFixed(0)}</span>
          )}
          {deal.validUntil && (
            <span
              className={`flex items-center gap-1 ${
                isExpired
                  ? 'text-rose-600 dark:text-rose-400 font-semibold'
                  : expiringSoon
                  ? 'text-amber-600 dark:text-amber-400 font-medium'
                  : ''
              }`}
            >
              <ClockIcon className="w-3.5 h-3.5" />
              {isExpired
                ? 'Expired'
                : days !== null && days <= 7
                ? `${days}d left`
                : `Until ${new Date(deal.validUntil).toLocaleDateString()}`}
            </span>
          )}
        </div>

        {/* Code + actions */}
        <div className="mt-4">
          <div className="flex items-stretch gap-2">
            <div className="flex-1 bg-emerald-50 dark:bg-emerald-900/20 border-2 border-dashed border-emerald-300 dark:border-emerald-800 rounded-lg px-3 py-2 font-mono text-sm font-semibold text-emerald-800 dark:text-emerald-300 text-center tracking-wider truncate">
              {deal.code}
            </div>
            <button
              onClick={() => onCopyCode(deal.code)}
              disabled={isExpired}
              className="px-3 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold flex items-center gap-1"
            >
              <ClipboardIcon className="w-4 h-4" />
              Copy
            </button>
          </div>
          <button
            onClick={() => onShowQr(deal)}
            disabled={isExpired}
            className="mt-2 w-full px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700/60 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-700 dark:text-gray-200 text-xs font-medium flex items-center justify-center gap-1.5"
          >
            <span className="text-base leading-none">▤</span> View QR & redeem
          </button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// QR Modal (also handles redeem-tracking)
// ─────────────────────────────────────────────────────────────────────────

const QrModal = ({
  deal,
  onClose,
}: {
  deal: Deal;
  onClose: () => void;
}) => {
  const { isAuthenticated } = useAuth();
  const [redeeming, setRedeeming] = useState(false);
  const [redeemed, setRedeemed] = useState(false);

  const handleRedeem = async () => {
    if (!isAuthenticated) {
      toast.error('Please sign in to track your redemptions.');
      return;
    }
    setRedeeming(true);
    try {
      const res = await redeemDeal(deal.code, deal.minSpend);
      if (res.success) {
        setRedeemed(true);
        toast.success(res.message || 'Redemption recorded — enjoy your trip!');
      } else {
        toast.error(res.message || 'Could not record redemption.');
      }
    } finally {
      setRedeeming(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="relative bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-sm w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
          aria-label="Close"
        >
          <XMarkIcon className="w-5 h-5 text-gray-500" />
        </button>

        <div className="text-center">
          <div className="inline-block rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-500 px-4 py-1.5 text-white text-sm font-bold mb-3">
            {formatDiscount(deal)}
          </div>
          <h3 className="font-bold text-gray-900 dark:text-white text-lg">
            {deal.title}
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {deal.partnerName}
            {deal.partnerDestination ? ` · ${deal.partnerDestination}` : ''}
          </p>

          <div className="my-5 flex justify-center">
            <div className="bg-white p-3 rounded-xl border border-gray-200 dark:border-gray-700 shadow-inner">
              <img
                src={qrSrc(deal.qrData, 200)}
                alt={`QR code for ${deal.code}`}
                width={200}
                height={200}
                className="block"
              />
            </div>
          </div>

          <div className="bg-emerald-50 dark:bg-emerald-900/20 border-2 border-dashed border-emerald-300 dark:border-emerald-800 rounded-lg px-3 py-2 font-mono text-base font-semibold text-emerald-800 dark:text-emerald-300 tracking-widest">
            {deal.code}
          </div>

          {deal.terms && (
            <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-3 italic leading-relaxed">
              {deal.terms}
            </p>
          )}

          <div className="mt-5 flex gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(deal.code);
                toast.success('Code copied!');
              }}
              className="flex-1 px-4 py-2.5 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 text-sm font-medium flex items-center justify-center gap-1.5"
            >
              <ClipboardIcon className="w-4 h-4" /> Copy code
            </button>
            <button
              onClick={handleRedeem}
              disabled={redeeming || redeemed}
              className={`flex-1 px-4 py-2.5 rounded-xl text-white text-sm font-semibold flex items-center justify-center gap-1.5 ${
                redeemed
                  ? 'bg-emerald-600'
                  : 'bg-teal-600 hover:bg-teal-700 disabled:opacity-60'
              }`}
            >
              {redeemed ? (
                <>
                  <CheckCircleIcon className="w-4 h-4" /> Redeemed
                </>
              ) : redeeming ? (
                'Recording…'
              ) : (
                'Mark as redeemed'
              )}
            </button>
          </div>

          <p className="mt-4 text-[10px] text-gray-400 dark:text-gray-500">
            Show this QR or code at the partner's counter to claim your
            discount.
          </p>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────

const DealsPage = () => {
  const { user, isAuthenticated } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [view, setView] = useState<ViewMode>('all');
  const [destination, setDestination] = useState(
    searchParams.get('destination') || '',
  );
  const [destinationDraft, setDestinationDraft] = useState(destination);
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [sortMode, setSortMode] = useState<SortMode>('expiring');
  const [qrDeal, setQrDeal] = useState<Deal | null>(null);

  // Re-render on saved-deals changes (cross-component event).
  const [savedSig, setSavedSig] = useState(0);
  useEffect(() => {
    const handler = () => setSavedSig((n) => n + 1);
    window.addEventListener(SAVED_DEALS_EVENT, handler);
    window.addEventListener('storage', handler);
    return () => {
      window.removeEventListener(SAVED_DEALS_EVENT, handler);
      window.removeEventListener('storage', handler);
    };
  }, []);

  // ── Fetch deals
  const dealsQuery = useQuery({
    queryKey: ['deals', destination, category],
    queryFn: () => getDealsList({ destination, category }),
    staleTime: 60_000,
  });

  // ── Pull user's destinations from their saved itineraries (logged-in only)
  // so we can show one-tap destination chips.
  const itinerariesQuery = useQuery({
    queryKey: ['my-trip-destinations'],
    queryFn: () => getItineraries(),
    enabled: !!isAuthenticated,
    staleTime: 5 * 60_000,
  });

  const tripDestinations = useMemo(() => {
    const items = itinerariesQuery.data || [];
    const seen = new Set<string>();
    const out: string[] = [];
    items.forEach((it) => {
      const d = (it.destination || '').trim();
      if (d && !seen.has(d.toLowerCase())) {
        seen.add(d.toLowerCase());
        out.push(d);
      }
    });
    return out.slice(0, 8);
  }, [itinerariesQuery.data]);

  // ── Saved/wallet deals (also re-pulled when storage changes)
  const savedDeals = useMemo(() => {
    void savedSig;
    return getSavedDeals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedSig]);

  const visibleDeals = useMemo(() => {
    const source = view === 'saved' ? savedDeals : dealsQuery.data || [];
    let list = [...source];

    // The saved-deals tab respects the same client-side filters so the user
    // can still narrow their wallet by destination/category.
    if (view === 'saved') {
      if (destination)
        list = list.filter((d) =>
          d.partnerDestination
            .toLowerCase()
            .includes(destination.toLowerCase()),
        );
      if (category) list = list.filter((d) => d.partnerCategory === category);
    }

    switch (sortMode) {
      case 'discount':
        list.sort((a, b) => {
          // Percentages first (sorted high→low), then fixed (sorted high→low)
          const score = (d: Deal) =>
            (d.discountType === 'percentage' ? 1000 : 0) + d.discountValue;
          return score(b) - score(a);
        });
        break;
      case 'newest':
        list.sort((a, b) => b.id - a.id);
        break;
      case 'expiring':
      default:
        list.sort((a, b) => {
          const da = daysUntilExpiry(a.validUntil);
          const db = daysUntilExpiry(b.validUntil);
          if (da === null && db === null) return 0;
          if (da === null) return 1;
          if (db === null) return -1;
          // Already-expired drift to the bottom
          if (da < 0 && db >= 0) return 1;
          if (db < 0 && da >= 0) return -1;
          return da - db;
        });
    }
    return list;
  }, [view, savedDeals, dealsQuery.data, destination, category, sortMode]);

  const applyDestinationFilter = (next: string) => {
    setDestination(next);
    setDestinationDraft(next);
    const sp = new URLSearchParams(searchParams);
    if (next) sp.set('destination', next);
    else sp.delete('destination');
    setSearchParams(sp, { replace: true });
  };

  const applyCategoryFilter = (next: string) => {
    setCategory(next);
    const sp = new URLSearchParams(searchParams);
    if (next) sp.set('category', next);
    else sp.delete('category');
    setSearchParams(sp, { replace: true });
  };

  const handleToggleSave = (deal: Deal) => {
    const wasSaved = isDealSaved(deal.id);
    toggleSavedDeal(deal);
    notifySavedDealsChanged();
    if (wasSaved) {
      toast('Removed from your travel wallet.', { icon: '🗑️' });
    } else {
      toast.success('Added to your travel wallet!');
    }
  };

  const handleCopy = (code: string) => {
    try {
      navigator.clipboard.writeText(code);
      toast.success(`Copied ${code}`);
    } catch {
      toast.error('Could not copy — long-press to copy manually.');
    }
  };

  const handleDownloadWallet = () => {
    const list =
      view === 'saved' ? visibleDeals : visibleDeals.slice(0, 30);
    if (list.length === 0) {
      toast.error('No deals to download.');
      return;
    }
    const subtitle = destination
      ? `Deals for ${destination}`
      : view === 'saved'
      ? 'Your saved deals'
      : 'Featured travel deals';
    const ok = printDealsAsWallet(list, {
      subtitle,
      travelerName: user?.first_name || user?.email || undefined,
    });
    if (!ok) {
      toast.error(
        'Pop-up blocked — please allow pop-ups for this site to download your wallet.',
      );
    }
  };

  const handleClearSaved = () => {
    visibleDeals.forEach((d) => removeSavedDeal(d.id));
    notifySavedDealsChanged();
    toast('Cleared your travel wallet.', { icon: '🧹' });
  };

  const loading = view === 'all' && dealsQuery.isLoading;
  const empty = !loading && visibleDeals.length === 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-br from-teal-600 via-emerald-600 to-cyan-600 dark:from-teal-800 dark:via-emerald-800 dark:to-cyan-800">
        <div className="absolute inset-0 opacity-15 pointer-events-none">
          <div className="absolute -top-24 -right-16 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/3 w-56 h-56 bg-emerald-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
          <div className="flex items-center gap-3 mb-3">
            <span className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-sm text-3xl">
              🎟️
            </span>
            <h1 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight">
              Deals & Coupons
            </h1>
          </div>
          <p className="text-teal-50 text-base md:text-lg max-w-2xl">
            Hand-picked discounts from our partner hotels, restaurants, tours,
            and attractions. Save deals to your travel wallet and download a
            print-ready PDF to take with you on your trip — works offline at
            the counter.
          </p>

          {/* Trip-destination chips */}
          {tripDestinations.length > 0 && (
            <div className="mt-6">
              <p className="text-teal-100 text-xs uppercase tracking-wider mb-2">
                Quick filter — your upcoming trips
              </p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => applyDestinationFilter('')}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                    destination === ''
                      ? 'bg-white text-teal-700 border-white'
                      : 'bg-white/10 text-white border-white/30 hover:bg-white/20'
                  }`}
                >
                  All destinations
                </button>
                {tripDestinations.map((d) => (
                  <button
                    key={d}
                    onClick={() => applyDestinationFilter(d)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all flex items-center gap-1 ${
                      destination.toLowerCase() === d.toLowerCase()
                        ? 'bg-white text-teal-700 border-white'
                        : 'bg-white/10 text-white border-white/30 hover:bg-white/20'
                    }`}
                  >
                    <MapPinIcon className="w-3 h-3" />
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Toolbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10 pb-12">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200/70 dark:border-gray-700/60 p-4 md:p-5 mb-6">
          <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center">
            {/* Tabs */}
            <div className="flex gap-1 p-1 rounded-xl bg-gray-100 dark:bg-gray-700/50 self-start">
              <button
                onClick={() => setView('all')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  view === 'all'
                    ? 'bg-white dark:bg-gray-800 text-teal-700 dark:text-teal-300 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                Browse Deals
              </button>
              <button
                onClick={() => setView('saved')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5 ${
                  view === 'saved'
                    ? 'bg-white dark:bg-gray-800 text-teal-700 dark:text-teal-300 shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                }`}
              >
                My Wallet
                {savedDeals.length > 0 && (
                  <span className="px-1.5 py-0.5 rounded-full bg-rose-500 text-white text-[10px] font-bold">
                    {savedDeals.length}
                  </span>
                )}
              </button>
            </div>

            {/* Destination input */}
            <div className="flex-1 flex gap-2">
              <div className="flex-1 relative">
                <MapPinIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={destinationDraft}
                  onChange={(e) => setDestinationDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter')
                      applyDestinationFilter(destinationDraft.trim());
                  }}
                  placeholder="Filter by city or country (e.g. Tokyo)"
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-teal-500 focus:outline-none"
                />
              </div>
              <button
                onClick={() => applyDestinationFilter(destinationDraft.trim())}
                className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium"
              >
                Search
              </button>
              {destination && (
                <button
                  onClick={() => applyDestinationFilter('')}
                  className="px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 text-sm"
                  aria-label="Clear destination filter"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Category + sort row */}
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700/60 flex flex-col md:flex-row gap-3 md:items-center">
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 shrink-0">
              <TagIcon className="w-4 h-4" /> Category
            </div>
            <div className="flex flex-wrap gap-1.5 flex-1">
              {CATEGORY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => applyCategoryFilter(opt.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all flex items-center gap-1 ${
                    category === opt.value
                      ? 'bg-teal-600 text-white border-teal-600'
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600 hover:border-teal-400'
                  }`}
                >
                  <span>{opt.icon}</span>
                  {opt.label}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 self-end md:self-auto">
              <label className="text-xs text-gray-500 dark:text-gray-400">
                Sort
              </label>
              <select
                value={sortMode}
                onChange={(e) => setSortMode(e.target.value as SortMode)}
                className="text-xs px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-200"
              >
                <option value="expiring">Expiring soon</option>
                <option value="discount">Best discount</option>
                <option value="newest">Newest</option>
              </select>
            </div>
          </div>

          {/* Action row */}
          <div className="mt-4 flex flex-wrap gap-2 items-center justify-between">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {loading
                ? 'Loading…'
                : visibleDeals.length === 0
                ? '0 deals'
                : `${visibleDeals.length} deal${
                    visibleDeals.length === 1 ? '' : 's'
                  }${destination ? ` for ${destination}` : ''}`}
            </p>
            <div className="flex gap-2">
              <button
                onClick={handleDownloadWallet}
                disabled={visibleDeals.length === 0}
                className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-40 text-white text-xs font-semibold flex items-center gap-1.5"
              >
                <ArrowDownTrayIcon className="w-4 h-4" /> Download wallet (PDF)
              </button>
              <button
                onClick={handleDownloadWallet}
                disabled={visibleDeals.length === 0}
                className="px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-40 text-gray-700 dark:text-gray-200 text-xs font-medium flex items-center gap-1.5"
              >
                <PrinterIcon className="w-4 h-4" /> Print
              </button>
              {view === 'saved' && savedDeals.length > 0 && (
                <button
                  onClick={handleClearSaved}
                  className="px-3 py-2 rounded-xl bg-rose-50 dark:bg-rose-900/20 hover:bg-rose-100 dark:hover:bg-rose-900/40 text-rose-700 dark:text-rose-300 text-xs font-medium"
                >
                  Clear wallet
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden animate-pulse"
              >
                <div className="h-20 bg-gradient-to-r from-gray-200 to-gray-100 dark:from-gray-700 dark:to-gray-700/60" />
                <div className="p-5 space-y-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded w-1/2" />
                  <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded w-full" />
                  <div className="h-9 bg-gray-100 dark:bg-gray-700 rounded mt-2" />
                </div>
              </div>
            ))}
          </div>
        ) : empty ? (
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm py-16 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-900/30 mb-4 text-3xl">
              {view === 'saved' ? '💼' : '🏷️'}
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
              {view === 'saved'
                ? 'Your travel wallet is empty'
                : 'No deals found'}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
              {view === 'saved'
                ? 'Tap the heart on any deal to save it here. Your wallet downloads as a PDF you can take on your trip.'
                : destination
                ? `We don't have active deals for "${destination}" yet. Try clearing the destination filter or browsing a different category.`
                : 'Check back soon — new partner deals are added regularly.'}
            </p>
            {view === 'saved' && (
              <button
                onClick={() => setView('all')}
                className="mt-5 px-5 py-2 rounded-xl bg-teal-600 text-white text-sm font-semibold hover:bg-teal-700"
              >
                Browse deals
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {visibleDeals.map((deal) => (
              <DealCard
                key={`${view}-${deal.id}`}
                deal={deal}
                saved={isDealSaved(deal.id)}
                onToggleSave={handleToggleSave}
                onCopyCode={handleCopy}
                onShowQr={setQrDeal}
              />
            ))}
          </div>
        )}

        {/* Footer help strip */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              icon: '🧭',
              title: 'Smart targeting',
              text: 'Use the chips above to instantly see deals around the destination of any trip you have planned.',
            },
            {
              icon: '💼',
              title: 'Travel wallet',
              text: 'Save deals you like — they live offline in your browser so you can reach for them later.',
            },
            {
              icon: '🖨️',
              title: 'Take it with you',
              text: 'Download your wallet as a PDF and show the code or QR at the partner counter to redeem.',
            },
          ].map((card) => (
            <div
              key={card.title}
              className="bg-white/80 dark:bg-gray-800/60 backdrop-blur-sm rounded-2xl border border-gray-200/60 dark:border-gray-700/50 p-5"
            >
              <div className="text-2xl mb-2">{card.icon}</div>
              <h4 className="font-semibold text-gray-900 dark:text-white text-sm">
                {card.title}
              </h4>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">
                {card.text}
              </p>
            </div>
          ))}
        </div>

        {/* Sign-in nudge for unauthenticated users */}
        {!isAuthenticated && (
          <div className="mt-6 bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-teal-900/30 dark:to-emerald-900/30 border border-teal-200 dark:border-teal-800 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div>
              <p className="font-semibold text-gray-900 dark:text-white">
                Sign in to track redemptions
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Logged-in travellers get personalised destination suggestions
                and a redemption history they can carry across devices.
              </p>
            </div>
            <Link
              to={ROUTES.LOGIN}
              className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold"
            >
              Sign in
            </Link>
          </div>
        )}
      </div>

      {qrDeal && <QrModal deal={qrDeal} onClose={() => setQrDeal(null)} />}
    </div>
  );
};

export default DealsPage;
