import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useRequireAuth } from '@/hooks/useAuth';
import { Card, Button } from '@/components/common';
import { ArrowLeftIcon, TrashIcon } from '@heroicons/react/24/outline';
import { createItinerary, getItinerary, updateItinerary, deleteItinerary } from '@/services/itineraryService';
import { ItineraryPDFViewer } from '@/components/ItineraryPDFViewer';
import DayByDayPlan from '@/components/DayByDayPlan';
import { API_BASE_URL } from '@/utils/constants';
import toast from 'react-hot-toast';

const STATUS_FLOW = ['draft', 'planned', 'approved', 'booked', 'active', 'completed'];

const STATUS_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  draft: { label: 'Draft', icon: '📝', color: 'bg-gray-200 dark:bg-gray-700' },
  planned: { label: 'Planned', icon: '📋', color: 'bg-blue-200 dark:bg-blue-800' },
  approved: { label: 'Approved', icon: '✅', color: 'bg-emerald-200 dark:bg-emerald-800' },
  booking: { label: 'Booking...', icon: '⏳', color: 'bg-yellow-200 dark:bg-yellow-800' },
  booked: { label: 'Booked', icon: '🎫', color: 'bg-indigo-200 dark:bg-indigo-800' },
  active: { label: 'Active', icon: '🚀', color: 'bg-green-200 dark:bg-green-800' },
  completed: { label: 'Completed', icon: '🏁', color: 'bg-purple-200 dark:bg-purple-800' },
  cancelled: { label: 'Cancelled', icon: '❌', color: 'bg-red-200 dark:bg-red-800' },
};

const ItineraryDetailPage = () => {
  const { user } = useRequireAuth();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNewItinerary = id === 'new';

  const [formData, setFormData] = useState({
    title: '',
    destination: '',
    start_date: '',
    end_date: '',
    description: '',
    number_of_travelers: 1,
    estimated_budget: '',
    currency: 'USD',
  });

  const [days, setDays] = useState<any[]>([]);
  const [itineraryStatus, setItineraryStatus] = useState('draft');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [booking, setBooking] = useState(false);
  const [bookingResult, setBookingResult] = useState<any>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const loadItinerary = useCallback(async (itineraryId: string) => {
    try {
      setLoading(true);
      const data = await getItinerary(itineraryId);
      setFormData({
        title: data.title,
        destination: data.destination,
        start_date: data.start_date,
        end_date: data.end_date,
        description: data.description || '',
        number_of_travelers: data.number_of_travelers,
        estimated_budget: data.estimated_budget || '',
        currency: data.currency || 'USD',
      });
      setDays(data.days || []);
      setItineraryStatus(data.status);
    } catch (err) {
      console.error('Failed to load itinerary:', err);
      toast.error('Failed to load itinerary');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isNewItinerary && id) {
      loadItinerary(id);
    }
  }, [id, isNewItinerary, loadItinerary]);

  const handleDaysUpdate = () => {
    if (id && !isNewItinerary) {
      loadItinerary(id);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isNewItinerary) {
        const dataWithUser = {
          ...formData,
          user: String(user.id),
          status: 'planned',
        };
        await createItinerary(dataWithUser);
        toast.success('Itinerary created!');
      } else if (id) {
        await updateItinerary(id, formData);
        toast.success('Itinerary updated!');
      }
      navigate('/itinerary');
    } catch (err: any) {
      let errorMessage = 'Failed to save itinerary';
      if (err.response?.data) {
        if (typeof err.response.data === 'object') {
          const errors = Object.entries(err.response.data)
            .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
            .join('; ');
          errorMessage = errors || errorMessage;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // ── Status Workflow Actions ──

  const authHeaders = (): Record<string, string> => {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  };

  const handleApprove = async () => {
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/itineraries/itineraries/${id}/approve/`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const data = await res.json();
      if (data.success) {
        setItineraryStatus('approved');
        toast.success('Plan approved! Ready to book.');
      } else {
        toast.error(data.error || 'Failed to approve');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed to approve');
    }
  };

  const handleReject = async () => {
    if (!id) return;
    const reason = prompt('Reason for sending back to draft (optional):');
    try {
      const res = await fetch(`${API_BASE_URL}/api/itineraries/itineraries/${id}/reject/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ reason: reason || '' }),
      });
      const data = await res.json();
      if (data.success) {
        setItineraryStatus('draft');
        toast.success('Sent back to draft for editing');
      } else {
        toast.error(data.error || 'Failed');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed');
    }
  };

  const handleBookAll = async () => {
    if (!id) return;
    setBooking(true);
    setBookingResult(null);

    try {
      const res = await fetch(`${API_BASE_URL}/api/itineraries/itineraries/${id}/book/`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const data = await res.json();
      setBookingResult(data);

      if (data.success) {
        setItineraryStatus('booked');
        toast.success(`All booked! Booking #${data.booking_number}`);
      } else if (data.items_failed > 0) {
        toast.error(`${data.items_failed} item(s) failed. ${data.items_booked} booked.`);
      } else {
        toast.error(data.error || 'Booking failed');
      }
    } catch (err: any) {
      toast.error(err.message || 'Booking failed');
    } finally {
      setBooking(false);
      if (id) loadItinerary(id);
    }
  };

  const handleStatusUpdate = async (newStatus: string) => {
    if (!id) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/itineraries/itineraries/${id}/update-status/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        setItineraryStatus(newStatus);
        toast.success(`Status updated to ${newStatus}`);
      } else {
        toast.error(data.error || 'Failed to update status');
      }
    } catch (err: any) {
      toast.error(err.message || 'Failed');
    }
  };

  const handleDeleteItinerary = async () => {
    if (!id || !deleteConfirm) return;
    try {
      await deleteItinerary(id);
      toast.success('Trip deleted');
      navigate('/itinerary');
    } catch (err: any) {
      toast.error(err.message || 'Failed to delete');
    }
  };

  const currentStepIdx = STATUS_FLOW.indexOf(itineraryStatus);
  const isCancelled = itineraryStatus === 'cancelled';

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <Button variant="ghost" onClick={() => navigate('/itinerary')}>
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Trips
          </Button>

          {!isNewItinerary && (
            <div className="flex items-center gap-2">
              {deleteConfirm ? (
                <>
                  <span className="text-sm text-red-600 dark:text-red-400 font-medium">Delete this trip?</span>
                  <Button
                    onClick={handleDeleteItinerary}
                    variant="secondary"
                    size="sm"
                    className="!bg-red-600 !text-white hover:!bg-red-700"
                  >
                    Yes, Delete
                  </Button>
                  <Button onClick={() => setDeleteConfirm(false)} variant="secondary" size="sm">
                    Cancel
                  </Button>
                </>
              ) : (
                <Button
                  onClick={() => setDeleteConfirm(true)}
                  variant="ghost"
                  size="sm"
                  className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <TrashIcon className="h-4 w-4 mr-1" />
                  Delete
                </Button>
              )}
            </div>
          )}
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {isNewItinerary ? 'Create New Trip' : formData.title || 'Edit Trip'}
        </h1>
      </div>

      {/* ── Status Progress Bar ── */}
      {!isNewItinerary && !isCancelled && (
        <Card className="mb-6">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Trip Status</h3>
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold ${STATUS_LABELS[itineraryStatus]?.color || ''}`}>
                {STATUS_LABELS[itineraryStatus]?.icon} {STATUS_LABELS[itineraryStatus]?.label || itineraryStatus}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {STATUS_FLOW.map((step, i) => {
                const isActive = i <= currentStepIdx;
                const isCurrent = step === itineraryStatus;
                return (
                  <div key={step} className="flex-1">
                    <div
                      className={`h-2 rounded-full transition-colors ${
                        isActive
                          ? isCurrent ? 'bg-primary-500' : 'bg-primary-300 dark:bg-primary-700'
                          : 'bg-gray-200 dark:bg-gray-700'
                      }`}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between mt-1 text-[10px] text-gray-400 dark:text-gray-500">
              {STATUS_FLOW.map((s) => (
                <span key={s} className={s === itineraryStatus ? 'font-bold text-primary-600 dark:text-primary-400' : ''}>
                  {STATUS_LABELS[s]?.label}
                </span>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* ── Human-in-the-Loop Actions ── */}
      {!isNewItinerary && (
        <Card className="mb-6">
          <div className="p-5">
            {(itineraryStatus === 'planned' || itineraryStatus === 'draft') && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {itineraryStatus === 'planned' ? '📋 Review & Approve Plan' : '📝 Draft — Finish Editing'}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {itineraryStatus === 'planned'
                      ? 'Review the day-by-day plan below. Edit anything, then approve to proceed to booking.'
                      : 'Complete your edits, then mark as planned when ready for review.'}
                  </p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  {itineraryStatus === 'draft' && (
                    <Button onClick={() => handleStatusUpdate('planned')} size="sm">
                      📋 Mark as Planned
                    </Button>
                  )}
                  {itineraryStatus === 'planned' && (
                    <>
                      <Button onClick={handleApprove} size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                        ✅ Approve Plan
                      </Button>
                      <Button onClick={handleReject} variant="secondary" size="sm">
                        ✏️ Send Back to Draft
                      </Button>
                    </>
                  )}
                </div>
              </div>
            )}

            {itineraryStatus === 'approved' && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">✅ Plan Approved — Ready to Book</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    The AI ReAct agent will book flights, hotels, restaurants, and activities.
                  </p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <Button onClick={handleBookAll} size="sm" disabled={booking} isLoading={booking} className="bg-indigo-600 hover:bg-indigo-700">
                    {booking ? 'Booking...' : '🎫 Book Everything'}
                  </Button>
                  <Button onClick={handleReject} variant="secondary" size="sm">✏️ Edit Plan</Button>
                </div>
              </div>
            )}

            {itineraryStatus === 'booking' && (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600 mx-auto mb-3"></div>
                <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Booking in Progress...</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">AI agent is booking your flights, hotels, and activities.</p>
              </div>
            )}

            {itineraryStatus === 'booked' && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">🎫 Everything Booked!</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">All items booked. Mark as active when your trip begins.</p>
                </div>
                <Button onClick={() => handleStatusUpdate('active')} size="sm" className="bg-green-600 hover:bg-green-700">
                  🚀 Start Trip
                </Button>
              </div>
            )}

            {itineraryStatus === 'active' && (
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">🚀 Trip In Progress!</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Have a wonderful trip! Mark as completed when you're back.</p>
                </div>
                <Button onClick={() => handleStatusUpdate('completed')} size="sm" className="bg-purple-600 hover:bg-purple-700">
                  🏁 Complete Trip
                </Button>
              </div>
            )}

            {itineraryStatus === 'completed' && (
              <div className="text-center py-2">
                <h3 className="font-semibold text-purple-700 dark:text-purple-300">🏁 Trip Completed</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Hope you had an amazing trip!</p>
              </div>
            )}

            {itineraryStatus === 'cancelled' && (
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-red-700 dark:text-red-300">❌ Trip Cancelled</h3>
                <Button onClick={() => handleStatusUpdate('draft')} variant="secondary" size="sm">Restore as Draft</Button>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* ── Booking Results ── */}
      {bookingResult && (
        <Card className="mb-6">
          <div className="p-5">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
              {bookingResult.success ? '🎉 Booking Summary' : '⚠️ Booking Results'}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
              <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">{bookingResult.items_booked || 0}</p>
                <p className="text-xs text-gray-500">Booked</p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">{bookingResult.items_skipped || 0}</p>
                <p className="text-xs text-gray-500">Skipped</p>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">{bookingResult.items_failed || 0}</p>
                <p className="text-xs text-gray-500">Failed</p>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">${(bookingResult.total_cost || 0).toLocaleString()}</p>
                <p className="text-xs text-gray-500">Total Cost</p>
              </div>
            </div>
            {bookingResult.booking_number && (
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Booking: <span className="font-mono font-bold">{bookingResult.booking_number}</span>
              </p>
            )}
            {bookingResult.booking_results?.length > 0 && (
              <div className="mt-3 space-y-1.5 max-h-48 overflow-y-auto">
                {bookingResult.booking_results.map((r: any, i: number) => (
                  <div key={i} className="flex items-center justify-between text-xs border-b border-gray-100 dark:border-gray-800 pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        ['booked', 'reserved', 'ticket_purchased'].includes(r.status)
                          ? 'bg-green-500'
                          : r.status === 'failed' ? 'bg-red-500' : 'bg-gray-400'
                      }`}></span>
                      <span className="text-gray-700 dark:text-gray-300 truncate max-w-[200px]">{r.item}</span>
                      <span className="text-gray-400 uppercase">{r.type}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {r.reference && <span className="font-mono text-gray-500">{r.reference}</span>}
                      {r.cost > 0 && <span className="font-medium">${r.cost}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Form */}
      <Card className="mb-6">
        {loading && !formData.title ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6 p-1">
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Trip Title *</label>
              <input type="text" id="title" name="title" required value={formData.title} onChange={handleChange}
                placeholder="e.g., Summer Vacation to Paris"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div>
              <label htmlFor="destination" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Destination *</label>
              <input type="text" id="destination" name="destination" required value={formData.destination} onChange={handleChange}
                placeholder="e.g., Paris, France"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Start Date *</label>
                <input type="date" id="start_date" name="start_date" required value={formData.start_date} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
              <div>
                <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">End Date *</label>
                <input type="date" id="end_date" name="end_date" required value={formData.end_date} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="number_of_travelers" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Travelers</label>
                <input type="number" id="number_of_travelers" name="number_of_travelers" min="1" value={formData.number_of_travelers} onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                />
              </div>
              <div>
                <label htmlFor="estimated_budget" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Budget</label>
                <div className="flex gap-2">
                  <input type="number" id="estimated_budget" name="estimated_budget" min="0" step="0.01" value={formData.estimated_budget} onChange={handleChange}
                    placeholder="1000"
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                  />
                  <select name="currency" value={formData.currency} onChange={handleChange}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                    <option value="JPY">JPY</option>
                    <option value="CAD">CAD</option>
                    <option value="AUD">AUD</option>
                  </select>
                </div>
              </div>
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</label>
              <textarea id="description" name="description" rows={3} value={formData.description} onChange={handleChange}
                placeholder="Describe your trip plans..."
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <div className="flex gap-4 justify-end">
              <Button type="button" variant="secondary" onClick={() => navigate('/itinerary')} disabled={loading}>Cancel</Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Saving...' : isNewItinerary ? 'Create Trip' : 'Save Changes'}
              </Button>
            </div>
          </form>
        )}
      </Card>

      {/* Day-by-Day Plan */}
      {!isNewItinerary && id && formData.start_date && formData.end_date && (
        <div className="mb-6">
          <DayByDayPlan
            itineraryId={Number(id)}
            days={days}
            startDate={formData.start_date}
            endDate={formData.end_date}
            onUpdate={handleDaysUpdate}
          />
        </div>
      )}

      {/* PDF Export & Email */}
      {!isNewItinerary && id && (
        <div className="mb-6">
          <ItineraryPDFViewer
            itineraryId={Number(id)}
            destination={formData.destination || 'Your Trip'}
          />
        </div>
      )}

      {/* Cancel Trip */}
      {!isNewItinerary && !['completed', 'cancelled'].includes(itineraryStatus) && (
        <div className="text-center mt-8 mb-4">
          <button
            onClick={() => handleStatusUpdate('cancelled')}
            className="text-sm text-red-500 hover:text-red-700 dark:hover:text-red-400 underline"
          >
            Cancel this trip
          </button>
        </div>
      )}
    </div>
  );
};

export default ItineraryDetailPage;
