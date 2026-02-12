/**
 * DayByDayPlan Component
 * Displays and manages day-by-day itinerary with activities
 */

import { useState } from 'react';
import {
  PlusIcon,
  TrashIcon,
  ClockIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline';
import {
  createItineraryDay,
  createItineraryItem,
  deleteItineraryDay,
  deleteItineraryItem,
} from '@/services/itineraryService';
import type { ItineraryDayData, ItineraryItemData } from '@/services/itineraryService';
import toast from 'react-hot-toast';

interface DayByDayPlanProps {
  itineraryId: number;
  days: ItineraryDayData[];
  startDate: string;
  endDate: string;
  onUpdate: () => void;
}

const ITEM_TYPE_ICONS: Record<string, string> = {
  flight: '✈️',
  hotel: '🏨',
  restaurant: '🍽️',
  attraction: '🗺️',
  activity: '🎯',
  transport: '🚗',
  note: '📝',
};

const ITEM_TYPE_COLORS: Record<string, string> = {
  flight: 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10',
  hotel: 'border-l-indigo-500 bg-indigo-50 dark:bg-indigo-900/10',
  restaurant: 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10',
  attraction: 'border-l-green-500 bg-green-50 dark:bg-green-900/10',
  activity: 'border-l-purple-500 bg-purple-50 dark:bg-purple-900/10',
  transport: 'border-l-cyan-500 bg-cyan-50 dark:bg-cyan-900/10',
  note: 'border-l-gray-500 bg-gray-50 dark:bg-gray-800',
};

const DayByDayPlan: React.FC<DayByDayPlanProps> = ({
  itineraryId,
  days,
  startDate,
  endDate,
  onUpdate,
}) => {
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set(days.map(d => d.id!)));
  const [addingItemForDay, setAddingItemForDay] = useState<number | null>(null);
  const [addingDay, setAddingDay] = useState(false);
  const [newDayTitle, setNewDayTitle] = useState('');
  const [newItem, setNewItem] = useState<Partial<ItineraryItemData>>({
    item_type: 'activity',
    title: '',
    description: '',
    start_time: '',
    location_name: '',
    estimated_cost: undefined,
  });

  const toggleDay = (dayId: number) => {
    setExpandedDays(prev => {
      const next = new Set(prev);
      if (next.has(dayId)) next.delete(dayId);
      else next.add(dayId);
      return next;
    });
  };

  const getDateForDayNumber = (dayNumber: number): string => {
    const start = new Date(startDate);
    start.setDate(start.getDate() + dayNumber - 1);
    return start.toISOString().split('T')[0];
  };

  const formatDate = (dateStr: string): string => {
    const d = new Date(dateStr + 'T00:00:00');
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const handleAddDay = async () => {
    const nextDayNumber = days.length > 0
      ? Math.max(...days.map(d => d.day_number)) + 1
      : 1;
    const dayDate = getDateForDayNumber(nextDayNumber);

    try {
      await createItineraryDay({
        itinerary: itineraryId,
        day_number: nextDayNumber,
        date: dayDate,
        title: newDayTitle || `Day ${nextDayNumber}`,
      });
      toast.success(`Day ${nextDayNumber} added`);
      setNewDayTitle('');
      setAddingDay(false);
      onUpdate();
    } catch (err) {
      toast.error('Failed to add day');
    }
  };

  const handleDeleteDay = async (dayId: number, dayNumber: number) => {
    if (!confirm(`Delete Day ${dayNumber} and all its activities?`)) return;
    try {
      await deleteItineraryDay(dayId);
      toast.success(`Day ${dayNumber} deleted`);
      onUpdate();
    } catch (err) {
      toast.error('Failed to delete day');
    }
  };

  const handleAddItem = async (dayId: number) => {
    if (!newItem.title?.trim()) {
      toast.error('Activity title is required');
      return;
    }

    try {
      await createItineraryItem({
        day: dayId,
        item_type: newItem.item_type || 'activity',
        title: newItem.title!,
        description: newItem.description || '',
        start_time: newItem.start_time || undefined,
        location_name: newItem.location_name || '',
        estimated_cost: newItem.estimated_cost || undefined,
      });
      toast.success('Activity added');
      setNewItem({ item_type: 'activity', title: '', description: '', start_time: '', location_name: '', estimated_cost: undefined });
      setAddingItemForDay(null);
      onUpdate();
    } catch (err) {
      toast.error('Failed to add activity');
    }
  };

  const handleDeleteItem = async (itemId: number) => {
    try {
      await deleteItineraryItem(itemId);
      toast.success('Activity removed');
      onUpdate();
    } catch (err) {
      toast.error('Failed to remove activity');
    }
  };

  const sortedDays = [...days].sort((a, b) => a.day_number - b.day_number);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Day-by-Day Plan
        </h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {days.length} day{days.length !== 1 ? 's' : ''} planned
        </span>
      </div>

      {sortedDays.length === 0 && !addingDay && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            No days planned yet. Start building your day-by-day itinerary!
          </p>
          <button
            onClick={() => setAddingDay(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            Add Day 1
          </button>
        </div>
      )}

      {sortedDays.map((day) => (
        <div
          key={day.id}
          className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden shadow-sm"
        >
          {/* Day Header */}
          <div
            className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
            onClick={() => toggleDay(day.id!)}
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-primary-600 dark:text-primary-400 font-bold text-sm">
                {day.day_number}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">
                  {day.title || `Day ${day.day_number}`}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(day.date)} {day.items?.length ? `\u00B7 ${day.items.length} activit${day.items.length === 1 ? 'y' : 'ies'}` : ''}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); handleDeleteDay(day.id!, day.day_number); }}
                className="p-1.5 text-gray-400 hover:text-red-500 rounded transition-colors"
                title="Delete day"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
              {expandedDays.has(day.id!) ? (
                <ChevronUpIcon className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronDownIcon className="h-5 w-5 text-gray-400" />
              )}
            </div>
          </div>

          {/* Day Content (expanded) */}
          {expandedDays.has(day.id!) && (
            <div className="px-5 pb-4 border-t border-gray-100 dark:border-gray-700">
              {day.notes && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 mb-3 italic">
                  {day.notes}
                </p>
              )}

              {/* Items */}
              <div className="space-y-2 mt-3">
                {(day.items || [])
                  .sort((a, b) => {
                    if (a.start_time && b.start_time) return a.start_time.localeCompare(b.start_time);
                    if (a.start_time) return -1;
                    if (b.start_time) return 1;
                    return (a.order || 0) - (b.order || 0);
                  })
                  .map((item) => (
                  <div
                    key={item.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border-l-4 ${ITEM_TYPE_COLORS[item.item_type] || ITEM_TYPE_COLORS.note}`}
                  >
                    <span className="text-lg flex-shrink-0 mt-0.5">
                      {ITEM_TYPE_ICONS[item.item_type] || '📌'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-medium text-gray-900 dark:text-white text-sm">
                          {item.title}
                        </h4>
                        <button
                          onClick={() => handleDeleteItem(item.id!)}
                          className="p-1 text-gray-300 hover:text-red-500 rounded transition-colors flex-shrink-0"
                        >
                          <TrashIcon className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      {item.description && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
                          {item.description}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                        {item.start_time && (
                          <span className="flex items-center gap-1">
                            <ClockIcon className="h-3 w-3" />
                            {item.start_time.slice(0, 5)}
                            {item.end_time && ` - ${item.end_time.slice(0, 5)}`}
                          </span>
                        )}
                        {item.location_name && (
                          <span className="flex items-center gap-1">
                            <MapPinIcon className="h-3 w-3" />
                            {item.location_name}
                          </span>
                        )}
                        {item.estimated_cost != null && Number(item.estimated_cost) > 0 && (
                          <span className="flex items-center gap-1">
                            <CurrencyDollarIcon className="h-3 w-3" />
                            ${Number(item.estimated_cost).toFixed(0)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add Item Form */}
              {addingItemForDay === day.id ? (
                <div className="mt-3 p-4 bg-gray-50 dark:bg-gray-700/30 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <select
                        value={newItem.item_type}
                        onChange={(e) => setNewItem(prev => ({ ...prev, item_type: e.target.value as any }))}
                        className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                      >
                        <option value="activity">Activity</option>
                        <option value="flight">Flight</option>
                        <option value="hotel">Hotel</option>
                        <option value="restaurant">Restaurant</option>
                        <option value="attraction">Attraction</option>
                        <option value="transport">Transport</option>
                        <option value="note">Note</option>
                      </select>
                      <input
                        type="text"
                        value={newItem.title}
                        onChange={(e) => setNewItem(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Activity title *"
                        className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                        autoFocus
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <input
                        type="time"
                        value={newItem.start_time}
                        onChange={(e) => setNewItem(prev => ({ ...prev, start_time: e.target.value }))}
                        className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                        placeholder="Time"
                      />
                      <input
                        type="text"
                        value={newItem.location_name}
                        onChange={(e) => setNewItem(prev => ({ ...prev, location_name: e.target.value }))}
                        placeholder="Location"
                        className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                      />
                      <input
                        type="number"
                        value={newItem.estimated_cost ?? ''}
                        onChange={(e) => setNewItem(prev => ({ ...prev, estimated_cost: e.target.value ? Number(e.target.value) : undefined }))}
                        placeholder="Cost ($)"
                        className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                      />
                    </div>
                    <input
                      type="text"
                      value={newItem.description}
                      onChange={(e) => setNewItem(prev => ({ ...prev, description: e.target.value }))}
                      placeholder="Description (optional)"
                      className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white"
                    />
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => {
                          setAddingItemForDay(null);
                          setNewItem({ item_type: 'activity', title: '', description: '', start_time: '', location_name: '', estimated_cost: undefined });
                        }}
                        className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleAddItem(day.id!)}
                        className="px-4 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setAddingItemForDay(day.id!)}
                  className="mt-3 flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                >
                  <PlusIcon className="h-4 w-4" />
                  Add activity
                </button>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Add Day */}
      {(sortedDays.length > 0 || addingDay) && (
        addingDay ? (
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={newDayTitle}
              onChange={(e) => setNewDayTitle(e.target.value)}
              placeholder={`Day ${days.length + 1} title (optional)`}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-800 dark:text-white text-sm"
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') handleAddDay(); }}
            />
            <button
              onClick={handleAddDay}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm transition-colors"
            >
              Add
            </button>
            <button
              onClick={() => { setAddingDay(false); setNewDayTitle(''); }}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setAddingDay(true)}
            className="w-full flex items-center justify-center gap-2 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-gray-500 dark:text-gray-400 hover:border-primary-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            <PlusIcon className="h-5 w-5" />
            Add Day {days.length + 1}
          </button>
        )
      )}
    </div>
  );
};

export default DayByDayPlan;
