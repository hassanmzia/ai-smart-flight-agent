import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MediaItem {
  id: number;
  user: string;
  destination: string;
  media_type: string;
  media_type_display: string;
  file: string;
  title: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  tags: string[];
  upvotes: number;
  created_at: string;
  is_owner?: boolean;
}

interface TravelStory {
  id: number;
  user: string;
  destination: string;
  title: string;
  content: string;
  language: string;
  cover_image: string;
  rating: number | null;
  upvotes: number;
  created_at: string;
  is_owner?: boolean;
}

interface TravelTip {
  id: number;
  user: string;
  destination: string;
  category: string;
  category_display: string;
  title: string;
  content: string;
  upvotes: number;
  created_at: string;
  is_owner?: boolean;
}

type TabKey = 'media' | 'stories' | 'tips';

// ---------------------------------------------------------------------------
// Tab config
// ---------------------------------------------------------------------------

const TABS: { key: TabKey; label: string; icon: string }[] = [
  { key: 'media', label: 'Photos & Media', icon: '\uD83D\uDCF8' },
  { key: 'stories', label: 'Travel Stories', icon: '\uD83D\uDCD6' },
  { key: 'tips', label: 'Tips & Tricks', icon: '\uD83D\uDCA1' },
];

const TIP_CATEGORIES = [
  { value: 'money_saving', label: 'Money Saving', emoji: '\uD83D\uDCB0' },
  { value: 'safety', label: 'Safety', emoji: '\uD83D\uDEE1\uFE0F' },
  { value: 'food', label: 'Food', emoji: '\uD83C\uDF7D\uFE0F' },
  { value: 'transport', label: 'Transport', emoji: '\uD83D\uDE8C' },
  { value: 'culture', label: 'Culture', emoji: '\uD83C\uDFAD' },
  { value: 'general', label: 'General', emoji: '\u2728' },
];

const MEDIA_TYPES = [
  { value: 'photo', label: 'Photo', accept: 'image/*' },
  { value: 'audio', label: 'Audio', accept: 'audio/*' },
  { value: 'video', label: 'Video', accept: 'video/*' },
  { value: 'pdf', label: 'PDF / Map', accept: '.pdf' },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<TabKey>('media');
  const [destination, setDestination] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Data states
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [stories, setStories] = useState<TravelStory[]>([]);
  const [tips, setTips] = useState<TravelTip[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showStoryModal, setShowStoryModal] = useState(false);
  const [showTipModal, setShowTipModal] = useState(false);

  // Lightbox
  const [selectedMedia, setSelectedMedia] = useState<MediaItem | null>(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string> = {};
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (destination.trim()) params.destination = destination.trim();

      const [mediaRes, storiesRes, tipsRes] = await Promise.all([
        api.get('/api/community/media/', { params }).catch(() => ({ data: { results: [] } })),
        api.get('/api/community/stories/', { params }).catch(() => ({ data: { results: [] } })),
        api.get('/api/community/tips/', { params }).catch(() => ({ data: { results: [] } })),
      ]);

      setMedia(mediaRes.data?.items || mediaRes.data?.results || (Array.isArray(mediaRes.data) ? mediaRes.data : []));
      setStories(storiesRes.data?.items || storiesRes.data?.results || (Array.isArray(storiesRes.data) ? storiesRes.data : []));
      setTips(tipsRes.data?.items || tipsRes.data?.results || (Array.isArray(tipsRes.data) ? tipsRes.data : []));
    } catch {
      // fail silently
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, destination]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpvote = async (type: string, id: number) => {
    try {
      await api.post(`/api/community/${type}/${id}/upvote/`);
      fetchData();
    } catch {
      // silently fail
    }
  };

  const handleDelete = async (type: 'media' | 'stories' | 'tips', id: number, label: string) => {
    if (!window.confirm(`Delete this ${label}? This action cannot be undone.`)) return;
    try {
      await api.delete(`/api/community/${type}/${id}/`);
      // Close the lightbox if the deleted item was open.
      setSelectedMedia(current => (current && current.id === id && type === 'media' ? null : current));
      fetchData();
    } catch {
      window.alert(`Could not delete this ${label}. Please try again.`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero */}
      <div className="bg-gradient-to-r from-teal-600 via-emerald-600 to-cyan-600 rounded-2xl shadow-lg p-8 mb-8 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Community Hub</h1>
            <p className="text-teal-100 text-sm max-w-lg">
              Share your travel photos, stories, and tips. Help fellow travelers discover the world through your experiences.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-4 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-white text-sm font-semibold transition-colors flex items-center gap-2"
            >
              {'\uD83D\uDCF7'} Upload Media
            </button>
            <button
              onClick={() => setShowStoryModal(true)}
              className="px-4 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-white text-sm font-semibold transition-colors flex items-center gap-2"
            >
              {'\u270D\uFE0F'} Write Story
            </button>
            <button
              onClick={() => setShowTipModal(true)}
              className="px-4 py-2.5 rounded-xl bg-white/20 hover:bg-white/30 text-white text-sm font-semibold transition-colors flex items-center gap-2"
            >
              {'\uD83D\uDCA1'} Share Tip
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="flex gap-3 mt-6">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search community content..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/40"
            />
          </div>
          <input
            type="text"
            placeholder="Filter by destination..."
            value={destination}
            onChange={e => setDestination(e.target.value)}
            className="w-48 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-white/40"
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700 pb-3">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
              activeTab === tab.key
                ? 'bg-teal-600 text-white shadow-md'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
            <span className="text-xs opacity-75">
              ({tab.key === 'media' ? media.length : tab.key === 'stories' ? stories.length : tips.length})
            </span>
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin inline-block w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full" />
          <p className="text-gray-500 dark:text-gray-400 mt-2 text-sm">Loading community content...</p>
        </div>
      )}

      {/* Media gallery */}
      {!isLoading && activeTab === 'media' && (
        <div>
          {media.length === 0 ? (
            <EmptyState
              emoji={'\uD83D\uDCF8'}
              title="No media yet"
              description="Be the first to share photos, audio, or videos from your travels!"
              action={() => setShowUploadModal(true)}
              actionLabel="Upload Media"
            />
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {media.map(item => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="group relative bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden cursor-pointer hover:shadow-lg transition-all"
                  onClick={() => setSelectedMedia(item)}
                >
                  {item.is_owner && (
                    <button
                      type="button"
                      onClick={e => { e.stopPropagation(); handleDelete('media', item.id, 'upload'); }}
                      aria-label="Delete this upload"
                      title="Delete this upload"
                      className="absolute top-2 right-2 z-10 inline-flex items-center justify-center w-8 h-8 rounded-full bg-white/90 dark:bg-gray-900/90 text-gray-600 dark:text-gray-300 hover:bg-red-500 hover:text-white shadow-md opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                    >
                      {'\uD83D\uDDD1\uFE0F'}
                    </button>
                  )}
                  {item.media_type === 'photo' ? (
                    <div className="aspect-square bg-gray-100 dark:bg-gray-700">
                      <img
                        src={item.file}
                        alt={item.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                      />
                    </div>
                  ) : (
                    <div className="aspect-square bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                      <span className="text-4xl">
                        {item.media_type === 'audio' ? '\uD83C\uDFB5' :
                         item.media_type === 'video' ? '\uD83C\uDFA5' :
                         item.media_type === 'pdf' ? '\uD83D\uDCC4' : '\uD83D\uDCC1'}
                      </span>
                    </div>
                  )}
                  <div className="p-3">
                    <h4 className="text-xs font-semibold text-gray-900 dark:text-white truncate">{item.title}</h4>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-[10px] text-gray-500 dark:text-gray-400">{item.destination}</span>
                      <button
                        onClick={e => { e.stopPropagation(); handleUpvote('media', item.id); }}
                        className="text-[10px] text-gray-400 hover:text-red-500 transition-colors flex items-center gap-0.5"
                      >
                        {'\u2764\uFE0F'} {item.upvotes}
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stories */}
      {!isLoading && activeTab === 'stories' && (
        <div>
          {stories.length === 0 ? (
            <EmptyState
              emoji={'\uD83D\uDCD6'}
              title="No stories yet"
              description="Share your travel adventures and inspire others!"
              action={() => setShowStoryModal(true)}
              actionLabel="Write a Story"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {stories.map(story => (
                <motion.div
                  key={story.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden hover:shadow-md transition-all"
                >
                  {story.cover_image && (
                    <img src={story.cover_image} alt={story.title} className="w-full h-40 object-cover" loading="lazy" />
                  )}
                  <div className="p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 font-medium">
                        {story.destination}
                      </span>
                      <span className="text-xs text-gray-400">{new Date(story.created_at).toLocaleDateString()}</span>
                    </div>
                    <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-2">{story.title}</h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-3 leading-relaxed">{story.content}</p>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                      <span className="text-xs text-gray-500">{story.user}</span>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleUpvote('stories', story.id)}
                          className="text-xs text-gray-400 hover:text-red-500 transition-colors flex items-center gap-1"
                        >
                          {'\u2764\uFE0F'} {story.upvotes}
                        </button>
                        {story.is_owner && (
                          <button
                            type="button"
                            onClick={() => handleDelete('stories', story.id, 'story')}
                            aria-label="Delete this story"
                            title="Delete this story"
                            className="text-xs text-gray-400 hover:text-red-600 transition-colors flex items-center gap-1"
                          >
                            {'\uD83D\uDDD1\uFE0F'} Delete
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tips */}
      {!isLoading && activeTab === 'tips' && (
        <div>
          {tips.length === 0 ? (
            <EmptyState
              emoji={'\uD83D\uDCA1'}
              title="No tips yet"
              description="Share your travel wisdom to help other travelers!"
              action={() => setShowTipModal(true)}
              actionLabel="Share a Tip"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {tips.map(tip => {
                const cat = TIP_CATEGORIES.find(c => c.value === tip.category);
                return (
                  <motion.div
                    key={tip.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-4 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl flex-shrink-0">{cat?.emoji || '\u2728'}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 font-medium">
                            {tip.category_display}
                          </span>
                          <span className="text-xs text-gray-400">{tip.destination}</span>
                        </div>
                        <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-1">{tip.title}</h3>
                        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">{tip.content}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">{tip.user}</span>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => handleUpvote('tips', tip.id)}
                              className="text-xs text-gray-400 hover:text-red-500 transition-colors flex items-center gap-1"
                            >
                              {'\u2764\uFE0F'} {tip.upvotes}
                            </button>
                            {tip.is_owner && (
                              <button
                                type="button"
                                onClick={() => handleDelete('tips', tip.id, 'tip')}
                                aria-label="Delete this tip"
                                title="Delete this tip"
                                className="text-xs text-gray-400 hover:text-red-600 transition-colors flex items-center gap-1"
                              >
                                {'\uD83D\uDDD1\uFE0F'} Delete
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Upload Media Modal */}
      <AnimatePresence>
        {showUploadModal && (
          <UploadMediaModal onClose={() => setShowUploadModal(false)} onSuccess={() => { setShowUploadModal(false); fetchData(); }} />
        )}
      </AnimatePresence>

      {/* Write Story Modal */}
      <AnimatePresence>
        {showStoryModal && (
          <WriteStoryModal onClose={() => setShowStoryModal(false)} onSuccess={() => { setShowStoryModal(false); fetchData(); }} />
        )}
      </AnimatePresence>

      {/* Share Tip Modal */}
      <AnimatePresence>
        {showTipModal && (
          <ShareTipModal onClose={() => setShowTipModal(false)} onSuccess={() => { setShowTipModal(false); fetchData(); }} />
        )}
      </AnimatePresence>

      {/* Media Lightbox */}
      <AnimatePresence>
        {selectedMedia && (
          <MediaLightbox
            media={selectedMedia}
            onClose={() => setSelectedMedia(null)}
            onDelete={id => handleDelete('media', id, 'upload')}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty State
// ---------------------------------------------------------------------------

function EmptyState({ emoji, title, description, action, actionLabel }: {
  emoji: string; title: string; description: string; action: () => void; actionLabel: string;
}) {
  return (
    <div className="text-center py-16">
      <span className="text-5xl block mb-4">{emoji}</span>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-gray-500 dark:text-gray-400 text-sm mb-6 max-w-md mx-auto">{description}</p>
      <button
        onClick={action}
        className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm transition-colors"
      >
        {actionLabel}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upload Media Modal
// ---------------------------------------------------------------------------

function UploadMediaModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [title, setTitle] = useState('');
  const [destinationName, setDestinationName] = useState('');
  const [description, setDescription] = useState('');
  const [mediaType, setMediaType] = useState('photo');
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !destinationName) return;

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('destination', destinationName);
      formData.append('description', description);
      formData.append('media_type', mediaType);

      await api.post('/api/community/media/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      onSuccess();
    } catch {
      // handle error
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentMediaConfig = MEDIA_TYPES.find(m => m.value === mediaType);

  return (
    <ModalWrapper onClose={onClose} title="Upload Media">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Media Type</label>
          <div className="flex gap-2">
            {MEDIA_TYPES.map(mt => (
              <button
                key={mt.value}
                type="button"
                onClick={() => setMediaType(mt.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  mediaType === mt.value
                    ? 'bg-teal-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }`}
              >
                {mt.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Sunset over the Bosphorus"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
          <input
            type="text"
            value={destinationName}
            onChange={e => setDestinationName(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Istanbul, Turkey"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">File *</label>
          <input
            type="file"
            accept={currentMediaConfig?.accept}
            onChange={e => setFile(e.target.files?.[0] || null)}
            required
            className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
          <textarea
            value={description}
            onChange={e => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Tell us about this..."
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !file || !title || !destinationName}
            className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {isSubmitting ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  );
}

// ---------------------------------------------------------------------------
// Write Story Modal
// ---------------------------------------------------------------------------

function WriteStoryModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [title, setTitle] = useState('');
  const [destinationName, setDestinationName] = useState('');
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !destinationName || !content) return;

    setIsSubmitting(true);
    try {
      await api.post('/api/community/stories/', { title, destination: destinationName, content });
      onSuccess();
    } catch {
      // handle error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ModalWrapper onClose={onClose} title="Write a Travel Story">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="My magical week in Kyoto"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
          <input
            type="text"
            value={destinationName}
            onChange={e => setDestinationName(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Kyoto, Japan"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Your Story *</label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            required
            rows={8}
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Share your travel experience..."
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !title || !destinationName || !content}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium disabled:opacity-50"
          >
            {isSubmitting ? 'Publishing...' : 'Publish Story'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  );
}

// ---------------------------------------------------------------------------
// Share Tip Modal
// ---------------------------------------------------------------------------

function ShareTipModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [title, setTitle] = useState('');
  const [destinationName, setDestinationName] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState('general');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !destinationName || !content) return;

    setIsSubmitting(true);
    try {
      await api.post('/api/community/tips/', { title, destination: destinationName, content, category });
      onSuccess();
    } catch {
      // handle error
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ModalWrapper onClose={onClose} title="Share a Travel Tip">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
          <div className="flex flex-wrap gap-2">
            {TIP_CATEGORIES.map(cat => (
              <button
                key={cat.value}
                type="button"
                onClick={() => setCategory(cat.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1 ${
                  category === cat.value
                    ? 'bg-amber-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                }`}
              >
                {cat.emoji} {cat.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
          <input
            type="text"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Use the metro instead of taxis"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
          <input
            type="text"
            value={destinationName}
            onChange={e => setDestinationName(e.target.value)}
            required
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Paris, France"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Tip Details *</label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            required
            rows={4}
            className="w-full rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm px-3 py-2"
            placeholder="Your travel wisdom..."
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700">
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !title || !destinationName || !content}
            className="px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium disabled:opacity-50"
          >
            {isSubmitting ? 'Sharing...' : 'Share Tip'}
          </button>
        </div>
      </form>
    </ModalWrapper>
  );
}

// ---------------------------------------------------------------------------
// Modal Wrapper
// ---------------------------------------------------------------------------

function ModalWrapper({ children, onClose, title }: { children: React.ReactNode; onClose: () => void; title: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-bold text-gray-900 dark:text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-4">{children}</div>
      </motion.div>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Media Lightbox
// ---------------------------------------------------------------------------

function MediaLightbox({
  media,
  onClose,
  onDelete,
}: {
  media: MediaItem;
  onClose: () => void;
  onDelete?: (id: number) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        exit={{ scale: 0.9 }}
        className="max-w-3xl w-full max-h-[90vh] overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {media.media_type === 'photo' ? (
          <img src={media.file} alt={media.title} className="w-full max-h-[70vh] object-contain rounded-2xl" />
        ) : media.media_type === 'audio' ? (
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
            <span className="text-6xl block mb-4">{'\uD83C\uDFB5'}</span>
            <audio controls src={media.file} className="w-full" />
          </div>
        ) : media.media_type === 'video' ? (
          <video controls src={media.file} className="w-full max-h-[70vh] rounded-2xl" />
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 text-center">
            <span className="text-6xl block mb-4">{'\uD83D\uDCC4'}</span>
            <a href={media.file} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">
              Open {media.title}
            </a>
          </div>
        )}
        <div className="mt-4 text-center">
          <h3 className="text-lg font-bold text-white">{media.title}</h3>
          {media.description && <p className="text-sm text-gray-300 mt-1">{media.description}</p>}
          <div className="flex items-center justify-center gap-3 mt-2 text-xs text-gray-400">
            <span>{media.destination}</span>
            <span>{media.user}</span>
            <span>{'\u2764\uFE0F'} {media.upvotes}</span>
          </div>
          {media.is_owner && onDelete && (
            <div className="mt-4">
              <button
                type="button"
                onClick={() => onDelete(media.id)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium transition-colors"
              >
                {'\uD83D\uDDD1\uFE0F'} Delete this upload
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}
