import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { useAuth, useRequireAuth } from '@/hooks/useAuth';
import {
  createSharedTrip,
  getInviteLink,
  getMyShared,
  getSharedWithMe,
  inviteCollaborators,
  joinByCode,
  removeCollaborator,
  type SharedTrip,
} from '@/services/collaborationService';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Loading from '@/components/common/Loading';
import { ROUTES } from '@/utils/constants';
import { formatDate } from '@/utils/formatters';
import { generateAndSaveAiItinerary } from '@/utils/aiItinerarySaver';

type Tab = 'my-trips' | 'create' | 'join';

const TripCard = ({
  trip,
  isOwner,
  ownerEmail,
  onInvite,
  onRemove,
  onCopyLink,
  inviteBusyId,
  copyBusyId,
}: {
  trip: SharedTrip;
  isOwner: boolean;
  ownerEmail: string;
  onInvite: (id: SharedTrip['id'], emails: string[]) => Promise<unknown>;
  onRemove: (id: SharedTrip['id'], email: string) => void;
  onCopyLink: (id: SharedTrip['id']) => void;
  inviteBusyId: string | null;
  copyBusyId: string | null;
}) => {
  const navigate = useNavigate();
  const [emailDraft, setEmailDraft] = useState('');

  const collaborators = (trip.shared_with || []).filter((e) => !!e);
  const tripIdStr = String(trip.id);
  const isInviting = inviteBusyId === tripIdStr;
  const isCopying = copyBusyId === tripIdStr;

  const submitInvite = async () => {
    const emails = emailDraft
      .split(/[\s,]+/)
      .map((e) => e.trim().toLowerCase())
      .filter((e) => e.includes('@'));
    if (emails.length === 0) {
      toast.error('Please enter at least one valid email');
      return;
    }
    await onInvite(trip.id, emails);
    setEmailDraft('');
  };

  return (
    <Card>
      <CardContent>
        <div className="p-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                {trip.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                {trip.destination} ·{' '}
                {trip.start_date && formatDate(trip.start_date, 'MMM dd')} -{' '}
                {trip.end_date && formatDate(trip.end_date, 'MMM dd, yyyy')} ·{' '}
                {collaborators.length + 1} member
                {collaborators.length === 0 ? '' : 's'}
              </p>
            </div>
            <div className="flex items-center gap-2 self-start">
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                  isOwner
                    ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                }`}
              >
                {isOwner ? 'Owner' : 'Collaborator'}
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => navigate(`/itineraries/${trip.id}`)}
              >
                Open trip →
              </Button>
            </div>
          </div>

          <div className="mb-5">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
              Team Members
            </h4>
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg px-3 py-2 border border-purple-100 dark:border-purple-900/40">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center text-white text-xs font-bold">
                  {(ownerEmail || 'U').charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {isOwner ? 'You' : ownerEmail || 'Owner'}
                  </p>
                  <span className="text-xs text-purple-700 dark:text-purple-300">
                    Owner
                  </span>
                </div>
              </div>
              {collaborators.map((email) => (
                <div
                  key={email}
                  className="flex items-center gap-2 bg-gray-50 dark:bg-gray-700/40 rounded-lg px-3 py-2 border border-gray-200/60 dark:border-gray-700/50"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-400 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
                    {email.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[180px]">
                      {email}
                    </p>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Editor
                    </span>
                  </div>
                  {isOwner && (
                    <button
                      onClick={() => onRemove(trip.id, email)}
                      className="ml-1 text-gray-400 hover:text-rose-500 transition-colors"
                      aria-label={`Remove ${email}`}
                      title="Remove"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              {collaborators.length === 0 && !isOwner && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No other collaborators yet.
                </p>
              )}
            </div>
          </div>

          {isOwner && (
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={emailDraft}
                  onChange={(e) => setEmailDraft(e.target.value)}
                  placeholder="email@example.com (comma- or space-separated)"
                  className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm"
                />
                <Button onClick={submitInvite} isLoading={isInviting}>
                  Send Invite
                </Button>
              </div>
              <button
                onClick={() => onCopyLink(trip.id)}
                disabled={isCopying}
                className="text-sm text-teal-600 dark:text-teal-400 hover:underline disabled:opacity-60"
              >
                {isCopying ? 'Generating link…' : '🔗 Copy invite link'}
              </button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

const CollaboratePage = () => {
  useRequireAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<Tab>('my-trips');

  // Create-trip form
  const [tripName, setTripName] = useState('');
  const [destination, setDestination] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [inviteEmails, setInviteEmails] = useState('');

  // AI-generation extras (mirrors AI Travel Planner inputs).
  const [useAi, setUseAi] = useState(true);
  const [originCity, setOriginCity] = useState('');
  const [travelers, setTravelers] = useState<number>(2);
  const [budget, setBudget] = useState('');
  const [interests, setInterests] = useState('');
  const [travelStyle, setTravelStyle] = useState('');
  const [aiBuilding, setAiBuilding] = useState(false);
  const [aiStatus, setAiStatus] = useState<string>('');

  // Join form
  const [joinCode, setJoinCode] = useState('');

  // Per-trip busy flags so spinners only show on the affected card.
  const [inviteBusyId, setInviteBusyId] = useState<string | null>(null);
  const [copyBusyId, setCopyBusyId] = useState<string | null>(null);

  // ── Load shared trips
  const { data: ownTrips, isLoading: loadingOwn } = useQuery({
    queryKey: ['collab', 'my-shared'],
    queryFn: getMyShared,
  });
  const { data: invitedTrips, isLoading: loadingInvited } = useQuery({
    queryKey: ['collab', 'shared-with-me'],
    queryFn: getSharedWithMe,
  });

  // ── Pre-fill destination (e.g. when navigated from a destination card)
  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // If a join code was supplied via ?join=…, hop to the join tab and prefill.
    const code = searchParams.get('join');
    if (code) {
      setJoinCode(code);
      setActiveTab('join');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  // ── Mutations
  const createMutation = useMutation({
    mutationFn: createSharedTrip,
    onSuccess: (trip) => {
      toast.success('Shared trip created!');
      queryClient.invalidateQueries({ queryKey: ['collab'] });
      queryClient.invalidateQueries({ queryKey: ['itineraries'] });
      // Reset form
      setTripName('');
      setStartDate('');
      setEndDate('');
      setInviteEmails('');
      setActiveTab('my-trips');
      // Optionally jump straight into the new trip
      navigate(`/itineraries/${trip.id}`);
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Could not create the trip');
    },
  });

  const inviteMutation = useMutation({
    mutationFn: ({
      tripId,
      emails,
    }: {
      tripId: SharedTrip['id'];
      emails: string[];
    }) => inviteCollaborators(tripId, emails),
    onMutate: ({ tripId }) => setInviteBusyId(String(tripId)),
    onSettled: () => setInviteBusyId(null),
    onSuccess: (res) => {
      const added = res?.added || [];
      if (added.length > 0) toast.success(`Invited ${added.length} collaborator(s)`);
      else toast('Already invited', { icon: 'ℹ️' });
      queryClient.invalidateQueries({ queryKey: ['collab'] });
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Failed to send invite');
    },
  });

  const removeMutation = useMutation({
    mutationFn: ({
      tripId,
      email,
    }: {
      tripId: SharedTrip['id'];
      email: string;
    }) => removeCollaborator(tripId, email),
    onSuccess: () => {
      toast.success('Collaborator removed');
      queryClient.invalidateQueries({ queryKey: ['collab'] });
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Could not remove collaborator');
    },
  });

  const joinMutation = useMutation({
    mutationFn: (code: string) => joinByCode(code),
    onSuccess: (res) => {
      toast.success(res?.message || 'Joined trip!');
      queryClient.invalidateQueries({ queryKey: ['collab'] });
      queryClient.invalidateQueries({ queryKey: ['itineraries'] });
      setJoinCode('');
      // Clear ?join= from URL after consumed.
      if (searchParams.has('join')) {
        searchParams.delete('join');
        setSearchParams(searchParams, { replace: true });
      }
      if (res?.itinerary?.id) navigate(`/itineraries/${res.itinerary.id}`);
      else setActiveTab('my-trips');
    },
    onError: (err: any) => {
      toast.error(err?.message || 'Invalid or expired invite code');
    },
  });

  const copyInviteLink = async (tripId: SharedTrip['id']) => {
    setCopyBusyId(String(tripId));
    try {
      const res = await getInviteLink(tripId);
      try {
        await navigator.clipboard.writeText(res.url);
        toast.success('Invite link copied to clipboard');
      } catch {
        // Fallback: show the link
        toast.success(`Invite link: ${res.url}`);
      }
    } catch (err: any) {
      toast.error(err?.message || 'Could not generate invite link');
    } finally {
      setCopyBusyId(null);
    }
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'my-trips', label: 'My Shared Trips', icon: '🗂️' },
    { id: 'create', label: 'Create Trip', icon: '➕' },
    { id: 'join', label: 'Join Trip', icon: '🔗' },
  ];

  const parseEmailList = (s: string) =>
    s
      .split(/[\s,\n]+/)
      .map((e) => e.trim().toLowerCase())
      .filter((e) => e.includes('@'));

  const resetCreateForm = () => {
    setTripName('');
    setStartDate('');
    setEndDate('');
    setInviteEmails('');
    setBudget('');
    setInterests('');
  };

  const submitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tripName.trim() || !destination.trim() || !startDate || !endDate) {
      toast.error('Trip name, destination, and dates are required');
      return;
    }
    if (endDate < startDate) {
      toast.error('End date must be after start date');
      return;
    }

    const emails = parseEmailList(inviteEmails);

    // ── Path A: AI-generated full itinerary (flights, hotels, dining, …)
    if (useAi) {
      if (!originCity.trim()) {
        toast.error('Origin city is required for AI generation');
        return;
      }
      setAiBuilding(true);
      setAiStatus('AI agents are searching flights, hotels, and activities…');
      try {
        const { itinerary } = await generateAndSaveAiItinerary(
          {
            origin_city: originCity.trim(),
            destination_city: destination.trim(),
            departure_date: startDate,
            return_date: endDate,
            passengers: travelers,
            budget: budget || undefined,
            travel_style: travelStyle || undefined,
            interests: interests || undefined,
          },
          {
            titleOverride: tripName.trim(),
            isShared: true,
            sharedWith: emails,
          },
        );
        setAiStatus('');
        toast.success('Shared trip created with full AI itinerary!');
        // Fire-and-forget: send invitations now that the trip exists.
        if (emails.length > 0) {
          inviteCollaborators(itinerary.id, emails).catch(() => {
            /* invites are best-effort; trip is already shared via shared_with */
          });
        }
        queryClient.invalidateQueries({ queryKey: ['collab'] });
        queryClient.invalidateQueries({ queryKey: ['itineraries'] });
        resetCreateForm();
        navigate(`/itineraries/${itinerary.id}`);
      } catch (err: any) {
        toast.error(
          err?.response?.data?.error || err?.message || 'AI planning failed',
        );
      } finally {
        setAiBuilding(false);
        setAiStatus('');
      }
      return;
    }

    // ── Path B: bare-bones shared trip (the original behavior)
    createMutation.mutate({
      title: tripName.trim(),
      destination: destination.trim(),
      start_date: startDate,
      end_date: endDate,
      invite_emails: emails,
    });
  };

  const own = ownTrips || [];
  const invited = invitedTrips || [];
  const trips = useMemo(() => {
    const map = new Map<string, { trip: SharedTrip; isOwner: boolean }>();
    own.forEach((t) => map.set(String(t.id), { trip: t, isOwner: true }));
    invited.forEach((t) => {
      const k = String(t.id);
      if (!map.has(k)) map.set(k, { trip: t, isOwner: false });
    });
    return Array.from(map.values());
  }, [own, invited]);

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-br from-teal-500 via-cyan-600 to-blue-600 dark:from-teal-800 dark:via-cyan-800 dark:to-blue-800">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-20 -right-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/4 w-48 h-48 bg-teal-300 rounded-full blur-3xl" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 md:py-14">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">
            👥 Collaborative Trip Planning
          </h1>
          <p className="text-cyan-100 text-lg">
            Plan trips together — invite friends and family by email, share an
            invite link, and edit the same itinerary as a team.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-6 relative z-10 pb-12">
        {/* Tabs */}
        <div className="flex gap-1.5 sm:gap-2 mb-6 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-5 py-2.5 rounded-xl font-medium text-xs sm:text-sm transition-all duration-200 whitespace-nowrap flex-shrink-0 ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg shadow-teal-500/25'
                  : 'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-gray-700 shadow-sm border border-gray-200/60 dark:border-gray-700/50'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* My Shared Trips */}
        {activeTab === 'my-trips' && (
          <div className="space-y-6">
            {loadingOwn || loadingInvited ? (
              <Card>
                <CardContent>
                  <div className="py-10">
                    <Loading text="Loading your shared trips..." />
                  </div>
                </CardContent>
              </Card>
            ) : trips.length === 0 ? (
              <Card>
                <CardContent>
                  <div className="text-center py-12">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-100 to-cyan-100 dark:from-teal-900/30 dark:to-cyan-900/30 mb-4">
                      <span className="text-3xl">👥</span>
                    </div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                      No shared trips yet
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 mb-6">
                      Create a trip and invite friends, or join one with an invite
                      code.
                    </p>
                    <div className="flex justify-center gap-3">
                      <Button onClick={() => setActiveTab('create')}>
                        Create Shared Trip
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => setActiveTab('join')}
                      >
                        Join with Code
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              trips.map(({ trip, isOwner }) => (
                <TripCard
                  key={trip.id}
                  trip={trip}
                  isOwner={isOwner}
                  ownerEmail={isOwner ? user?.email || '' : ''}
                  inviteBusyId={inviteBusyId}
                  copyBusyId={copyBusyId}
                  onInvite={(id, emails) =>
                    inviteMutation.mutateAsync({ tripId: id, emails })
                  }
                  onRemove={(id, email) =>
                    removeMutation.mutate({ tripId: id, email })
                  }
                  onCopyLink={(id) => copyInviteLink(id)}
                />
              ))
            )}
          </div>
        )}

        {/* Create Trip */}
        {activeTab === 'create' && (
          <Card>
            <CardHeader>
              <CardTitle>Create a Shared Trip</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={submitCreate} className="space-y-6 max-w-2xl">
                {/* AI toggle */}
                <div
                  className={`rounded-2xl border p-4 transition-colors ${
                    useAi
                      ? 'border-teal-200 dark:border-teal-800 bg-gradient-to-br from-teal-50 to-cyan-50 dark:from-teal-900/20 dark:to-cyan-900/20'
                      : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/40'
                  }`}
                >
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useAi}
                      onChange={(e) => setUseAi(e.target.checked)}
                      className="mt-1 w-4 h-4 rounded text-teal-600 focus:ring-teal-500"
                    />
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white text-sm">
                        ✨ Auto-build a complete itinerary with AI
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                        Generates day-by-day activities, recommended flights,
                        hotels, restaurants, and attractions — exactly like the
                        AI Travel Planner. Your collaborators land on a fully
                        populated trip with Flights / Hotels / Cars / Dining
                        tabs. Takes about a minute.
                      </p>
                    </div>
                  </label>
                </div>

                <Input
                  label="Trip Name"
                  value={tripName}
                  onChange={(e) => setTripName(e.target.value)}
                  placeholder="e.g., Tokyo Adventure 2026"
                  required
                />

                {useAi && (
                  <Input
                    label="From (Origin City)"
                    value={originCity}
                    onChange={(e) => setOriginCity(e.target.value)}
                    placeholder="e.g., New York"
                    required={useAi}
                  />
                )}

                <Input
                  label={useAi ? 'To (Destination City)' : 'Destination'}
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g., Tokyo, Japan"
                  required
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Start Date"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                  />
                  <Input
                    label="End Date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                  />
                </div>

                {useAi && (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <Input
                        label="Travelers"
                        type="number"
                        min={1}
                        value={travelers}
                        onChange={(e) =>
                          setTravelers(Math.max(1, Number(e.target.value)))
                        }
                      />
                      <Input
                        label="Budget USD (optional)"
                        type="number"
                        value={budget}
                        onChange={(e) => setBudget(e.target.value)}
                        placeholder="e.g., 3000"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                        Travel Style (optional)
                      </label>
                      <select
                        value={travelStyle}
                        onChange={(e) => setTravelStyle(e.target.value)}
                        className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                      >
                        <option value="">Any Style</option>
                        {[
                          'Budget',
                          'Comfort',
                          'Luxury',
                          'Adventure',
                          'Cultural',
                          'Family',
                          'Romantic',
                          'Business',
                        ].map((s) => (
                          <option key={s} value={s.toLowerCase()}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1.5">
                        Group Interests (optional)
                      </label>
                      <textarea
                        value={interests}
                        onChange={(e) => setInterests(e.target.value)}
                        rows={3}
                        placeholder="e.g., temples, ramen, anime stores, nightlife, day trips to Mt. Fuji"
                        className="w-full px-4 py-2.5 border border-gray-200 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                      />
                    </div>
                  </>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Invite Collaborators (optional)
                  </label>
                  <textarea
                    value={inviteEmails}
                    onChange={(e) => setInviteEmails(e.target.value)}
                    placeholder="alice@example.com, bob@example.com"
                    rows={2}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Separate multiple emails with commas, spaces, or new lines.
                    They'll receive an email invite.
                  </p>
                </div>

                {aiBuilding && (
                  <div className="rounded-xl bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-800 p-4">
                    <Loading
                      text={aiStatus || 'Building your shared itinerary…'}
                    />
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  isLoading={createMutation.isPending || aiBuilding}
                  disabled={createMutation.isPending || aiBuilding}
                >
                  {useAi
                    ? '✨ Generate & Share Trip'
                    : 'Create Shared Trip'}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Join Trip */}
        {activeTab === 'join' && (
          <Card>
            <CardHeader>
              <CardTitle>Join an Existing Trip</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!joinCode.trim()) {
                    toast.error('Paste the invite code');
                    return;
                  }
                  joinMutation.mutate(joinCode.trim());
                }}
                className="max-w-lg space-y-6"
              >
                <p className="text-gray-600 dark:text-gray-400">
                  Paste the invite code (or full invite URL) shared by your trip
                  organizer to join their collaborative trip.
                </p>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Invite Code
                  </label>
                  <textarea
                    value={joinCode}
                    onChange={(e) => {
                      const v = e.target.value;
                      // If user pasted a full URL, extract the code from ?join=…
                      const match = v.match(/[?&]join=([^&\s]+)/);
                      setJoinCode(match ? decodeURIComponent(match[1]) : v);
                    }}
                    rows={3}
                    placeholder="Paste invite code or invite URL here…"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent text-sm font-mono"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  isLoading={joinMutation.isPending}
                >
                  Join Trip
                </Button>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Tip: ask the trip owner to use "🔗 Copy invite link" on a
                  shared trip — they'll get a one-click link they can send you.
                </p>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Heads-up about feature scope */}
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-8 text-center">
          Heads up: voting on options and per-collaborator role permissions are
          coming soon. For now, all invited collaborators have edit access to
          the trip itinerary via{' '}
          <button
            onClick={() => navigate(ROUTES.ITINERARY)}
            className="text-teal-600 dark:text-teal-400 hover:underline"
          >
            My Trips
          </button>
          .
        </p>
      </div>
    </div>
  );
};

export default CollaboratePage;
