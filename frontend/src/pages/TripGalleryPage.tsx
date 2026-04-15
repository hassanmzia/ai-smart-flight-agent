import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface TemplateComment {
  id: number;
  user: string;
  user_id?: number | string;
  content: string;
  created_at: string;
}

interface TripTemplate {
  id: number;
  title: string;
  description: string;
  destination: string;
  country: string;
  duration_days: number;
  style: string;
  estimated_budget: number;
  currency: string;
  cover_image_url: string;
  tags: string[];
  highlights: string[];
  itinerary_data: Array<{ day: number; activities: Array<{ time: string; title: string; description: string; category: string; cost: number }> }>;
  is_featured: boolean;
  is_verified: boolean;
  clone_count: number;
  likes_count: number;
  dislikes_count?: number;
  comments_count?: number;
  views_count: number;
  rating: number;
  rating_count: number;
  my_reaction?: 'like' | 'dislike' | null;
  creator_name?: string;
  created_at: string;
}

const STYLES = [
  { value: '', label: 'All Styles' },
  { value: 'adventure', label: 'Adventure' }, { value: 'luxury', label: 'Luxury' },
  { value: 'budget', label: 'Budget' }, { value: 'cultural', label: 'Cultural' },
  { value: 'romantic', label: 'Romantic' }, { value: 'family', label: 'Family' },
  { value: 'solo', label: 'Solo' }, { value: 'foodie', label: 'Foodie' },
  { value: 'spiritual', label: 'Spiritual' }, { value: 'nature', label: 'Nature' },
];

const STYLE_EMOJIS: Record<string, string> = {
  adventure: '🏔️', luxury: '💎', budget: '💰', cultural: '🎭', romantic: '💕',
  family: '👨‍👩‍👧‍👦', solo: '🎒', foodie: '🍜', spiritual: '🕊️', nature: '🌿',
};

const SORT_OPTIONS = [
  { value: 'popular', label: 'Most Cloned' },
  { value: 'newest', label: 'Newest' },
  { value: 'rating', label: 'Top Rated' },
  { value: 'budget_low', label: 'Budget (Low)' },
];

type Tab = 'browse' | 'create' | 'my-templates';

export default function TripGalleryPage() {
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuth();
  const currentUserId = user?.id;
  const [tab, setTab] = useState<Tab>('browse');
  const [templates, setTemplates] = useState<TripTemplate[]>([]);
  const [featured, setFeatured] = useState<TripTemplate[]>([]);
  const [myTemplates, setMyTemplates] = useState<TripTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState<TripTemplate | null>(null);
  const [comments, setComments] = useState<TemplateComment[]>([]);
  const [commentText, setCommentText] = useState('');
  const [destination, setDestination] = useState('');
  const [style, setStyle] = useState('');
  const [sortBy, setSortBy] = useState('popular');

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const [genForm, setGenForm] = useState({ destination: '', duration_days: 3, style: 'adventure', budget: 0 });
  const [generating, setGenerating] = useState(false);

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { sort_by: sortBy };
      if (destination) params.destination = destination;
      if (style) params.style = style;
      const res = await api.get('/api/agents/templates/browse', { params });
      const items = res.data?.templates || res.data?.items || res.data;
      setTemplates(Array.isArray(items) ? items : []);
    } catch { setTemplates([]); }
    finally { setLoading(false); }
  }, [destination, style, sortBy]);

  const fetchFeatured = useCallback(async () => {
    try {
      const res = await api.get('/api/agents/templates/featured');
      const items = res.data?.templates || res.data;
      setFeatured(Array.isArray(items) ? items : []);
    } catch { setFeatured([]); }
  }, []);

  const fetchMyTemplates = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/api/agents/templates/mine');
      const items = res.data?.templates || res.data;
      setMyTemplates(Array.isArray(items) ? items : []);
    } catch { setMyTemplates([]); }
    finally { setLoading(false); }
  }, [isAuthenticated]);

  useEffect(() => {
    if (tab === 'browse') { fetchTemplates(); fetchFeatured(); }
    else if (tab === 'my-templates') fetchMyTemplates();
  }, [tab, fetchTemplates, fetchFeatured, fetchMyTemplates]);

  const loadComments = useCallback(async (templateId: number) => {
    try {
      const res = await api.get('/api/agents/templates/comments', { params: { template_id: templateId } });
      const items = res.data?.comments;
      setComments(Array.isArray(items) ? items : []);
    } catch { setComments([]); }
  }, []);

  const viewTemplate = async (id: number) => {
    try {
      const res = await api.get(`/api/agents/templates/${id}`);
      const t: TripTemplate | null = res.data?.template || null;
      setDetail(t);
      if (t) loadComments(t.id);
    } catch { toast.error('Template not found'); }
  };

  const cloneTemplate = async (id: number) => {
    try {
      await api.post('/api/agents/templates/clone', { template_id: id });
      toast.success('Trip cloned to your itineraries!');
    } catch { toast.error('Sign in to clone trips'); }
  };

  const applyReactionT = (t: TripTemplate, reaction: 'like' | 'dislike'): TripTemplate => {
    const current = t.my_reaction;
    let likes = t.likes_count;
    let dislikes = t.dislikes_count ?? 0;
    let next: 'like' | 'dislike' | null = reaction;
    if (current === reaction) {
      next = null;
      if (reaction === 'like') likes -= 1; else dislikes -= 1;
    } else {
      if (current === 'like') likes -= 1;
      if (current === 'dislike') dislikes -= 1;
      if (reaction === 'like') likes += 1; else dislikes += 1;
    }
    return {
      ...t,
      my_reaction: next,
      likes_count: Math.max(0, likes),
      dislikes_count: Math.max(0, dislikes),
    };
  };

  const reactTemplate = async (t: TripTemplate, reaction: 'like' | 'dislike') => {
    if (!isAuthenticated) { toast.error('Sign in to react'); return; }
    const updated = applyReactionT(t, reaction);
    setTemplates(prev => prev.map(x => x.id === t.id ? { ...x, ...updated } : x));
    setFeatured(prev => prev.map(x => x.id === t.id ? { ...x, ...updated } : x));
    setMyTemplates(prev => prev.map(x => x.id === t.id ? { ...x, ...updated } : x));
    if (detail?.id === t.id) setDetail({ ...detail, ...updated });
    try {
      const res = await api.post('/api/agents/templates/react', {
        template_id: t.id, reaction,
      });
      if (res.data?.success) {
        const patched = {
          my_reaction: res.data.my_reaction ?? null,
          likes_count: res.data.likes_count,
          dislikes_count: res.data.dislikes_count,
        };
        setTemplates(prev => prev.map(x => x.id === t.id ? { ...x, ...patched } : x));
        setFeatured(prev => prev.map(x => x.id === t.id ? { ...x, ...patched } : x));
        setMyTemplates(prev => prev.map(x => x.id === t.id ? { ...x, ...patched } : x));
        if (detail?.id === t.id) setDetail(d => d ? { ...d, ...patched } : d);
      }
    } catch {
      // Rollback
      setTemplates(prev => prev.map(x => x.id === t.id ? t : x));
      setFeatured(prev => prev.map(x => x.id === t.id ? t : x));
      setMyTemplates(prev => prev.map(x => x.id === t.id ? t : x));
      if (detail?.id === t.id) setDetail(t);
      toast.error('Failed to react');
    }
  };

  const addTemplateComment = async () => {
    if (!detail || !commentText.trim()) return;
    if (!isAuthenticated) { toast.error('Sign in to comment'); return; }
    try {
      const res = await api.post('/api/agents/templates/comments', {
        template_id: detail.id, content: commentText,
      });
      if (res.data?.success) {
        setComments(prev => [res.data.comment, ...prev]);
        setDetail(d => d ? { ...d, comments_count: res.data.comments_count ?? (d.comments_count ?? 0) + 1 } : d);
        setCommentText('');
        toast.success('Comment posted');
      } else {
        toast.error(res.data?.error || 'Comment failed');
      }
    } catch { toast.error('Failed to add comment'); }
  };

  const deleteTemplateComment = async (commentId: number) => {
    if (!detail) return;
    try {
      const res = await api.delete(`/api/agents/templates/comments/${commentId}`);
      if (res.data?.success) {
        setComments(prev => prev.filter(c => c.id !== commentId));
        setDetail(d => d ? {
          ...d,
          comments_count: res.data.comments_count ?? Math.max(0, (d.comments_count ?? 1) - 1),
        } : d);
        toast.success('Comment deleted');
      } else {
        toast.error(res.data?.error || 'Delete failed');
      }
    } catch { toast.error('Failed to delete'); }
  };

  const shareTemplate = async (t: TripTemplate) => {
    const url = `${window.location.origin}/gallery?template=${t.id}`;
    const shareData = { title: t.title, text: `${t.title} – a trip template on AI Smart Trip Planner`, url };
    try {
      if (navigator.share) await navigator.share(shareData);
      else {
        await navigator.clipboard.writeText(url);
        toast.success('Share link copied!');
      }
    } catch (err) {
      if ((err as { name?: string })?.name !== 'AbortError') {
        try {
          await navigator.clipboard.writeText(url);
          toast.success('Share link copied!');
        } catch { toast.error('Failed to share'); }
      }
    }
  };

  const generateTemplate = async () => {
    if (!genForm.destination) { toast.error('Enter a destination'); return; }
    setGenerating(true);
    try {
      const res = await api.post('/api/agents/templates/generate', genForm);
      if (res.data?.success) {
        toast.success('Template generated!');
        setTab('my-templates');
        fetchMyTemplates();
      }
    } catch { toast.error('Generation failed'); }
    finally { setGenerating(false); }
  };

  const renderStars = (rating: number) => {
    return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
  };

  // Template Detail View
  if (detail) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <button onClick={() => setDetail(null)} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-6">&larr; Back</button>
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="bg-gradient-to-r from-violet-500 to-purple-500 px-6 py-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{STYLE_EMOJIS[detail.style] || '✈️'}</span>
                {detail.is_verified && <span className="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">Verified</span>}
                {detail.is_featured && <span className="bg-yellow-400/30 text-white text-xs px-2 py-0.5 rounded-full">Featured</span>}
              </div>
              <h1 className="text-2xl font-bold text-white">{detail.title}</h1>
              <p className="text-violet-100 mt-1">{detail.destination}{detail.country && `, ${detail.country}`} &middot; {detail.duration_days} days &middot; ${detail.estimated_budget} {detail.currency}</p>
            </div>
            <div className="p-6">
              <p className="text-gray-700 dark:text-gray-300 mb-6">{detail.description}</p>

              {detail.highlights?.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-2">Highlights</h3>
                  <div className="flex flex-wrap gap-2">
                    {detail.highlights.map((h, i) => (
                      <span key={i} className="px-3 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400 rounded-lg text-sm">{h}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Itinerary */}
              {detail.itinerary_data?.length > 0 && (
                <div className="space-y-4">
                  <h3 className="font-bold text-gray-900 dark:text-white">Day-by-Day Itinerary</h3>
                  {detail.itinerary_data.map((day, i) => (
                    <div key={i} className="bg-gray-50 dark:bg-gray-700 rounded-xl p-4">
                      <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Day {day.day}</h4>
                      <div className="space-y-2">
                        {day.activities?.map((act, j) => (
                          <div key={j} className="flex items-start gap-3">
                            <span className="text-xs text-gray-400 w-14 flex-shrink-0 pt-0.5">{act.time}</span>
                            <div className="flex-1">
                              <span className="font-medium text-gray-800 dark:text-gray-200 text-sm">{act.title}</span>
                              {act.description && <p className="text-xs text-gray-500 mt-0.5">{act.description}</p>}
                            </div>
                            {act.cost > 0 && <span className="text-xs text-green-600">${act.cost}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 flex-wrap">
                <button onClick={() => cloneTemplate(detail.id)} className="px-5 py-2 bg-violet-600 text-white rounded-lg font-medium text-sm hover:bg-violet-700">
                  Clone This Trip ({detail.clone_count})
                </button>
                <button
                  onClick={() => reactTemplate(detail, 'like')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                    detail.my_reaction === 'like'
                      ? 'bg-pink-500 text-white'
                      : 'bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 hover:bg-pink-200'
                  }`}
                  aria-pressed={detail.my_reaction === 'like'}
                >
                  <span>👍</span><span>{detail.likes_count}</span>
                </button>
                <button
                  onClick={() => reactTemplate(detail, 'dislike')}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                    detail.my_reaction === 'dislike'
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  aria-pressed={detail.my_reaction === 'dislike'}
                >
                  <span>👎</span><span>{detail.dislikes_count ?? 0}</span>
                </button>
                <span className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-500">
                  💬 {detail.comments_count ?? comments.length}
                </span>
                <button
                  onClick={() => shareTemplate(detail)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200"
                >
                  🔗 Share
                </button>
                <span className="text-sm text-yellow-500 ml-2">{renderStars(detail.rating)} ({detail.rating_count})</span>
                <span className="text-xs text-gray-400 ml-auto">by {detail.creator_name || 'Traveler'}</span>
              </div>

              {/* Comments */}
              <div className="mt-6">
                <h3 className="font-bold text-gray-900 dark:text-white mb-3">Comments</h3>
                {comments.length === 0 && (
                  <p className="text-sm text-gray-400">No comments yet — be the first to discuss this trip!</p>
                )}
                {comments.map(c => {
                  const isOwn = currentUserId != null && String(c.user_id) === String(currentUserId);
                  return (
                    <div key={c.id} className="py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                      <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                        <span className="font-medium text-gray-700 dark:text-gray-300">{c.user}</span>
                        <span>{new Date(c.created_at).toLocaleDateString()}</span>
                        {isOwn && (
                          <button
                            onClick={() => deleteTemplateComment(c.id)}
                            className="ml-auto text-red-400 hover:text-red-600"
                          >Delete</button>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{c.content}</p>
                    </div>
                  );
                })}
                {isAuthenticated && (
                  <div className="flex gap-2 mt-3">
                    <input
                      value={commentText}
                      onChange={e => setCommentText(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') addTemplateComment(); }}
                      placeholder="Share your thoughts on this trip..."
                      className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <button onClick={addTemplateComment} className="px-4 py-2 bg-violet-500 text-white rounded-lg text-sm hover:bg-violet-600">Post</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'browse', label: 'Browse Trips', icon: '🌍' },
    { id: 'create', label: 'Create Template', icon: '✨' },
    { id: 'my-templates', label: 'My Templates', icon: '📋' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-violet-600 via-purple-600 to-indigo-600 dark:from-violet-800 dark:via-purple-800 dark:to-indigo-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2">Trip Gallery</h1>
          <p className="text-violet-100 text-lg">Browse, clone & customize trips from the community</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-violet-600 text-white shadow-lg' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
              }`}>
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {/* Browse */}
        {tab === 'browse' && (
          <div>
            {/* Featured */}
            {featured.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Featured Trips</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {featured.slice(0, 3).map(t => (
                    <button key={t.id} onClick={() => viewTemplate(t.id)} className="text-left bg-gradient-to-br from-violet-500 to-purple-500 rounded-2xl p-5 text-white hover:shadow-xl transition-shadow">
                      <span className="text-2xl">{STYLE_EMOJIS[t.style] || '✈️'}</span>
                      <h3 className="font-bold text-lg mt-2">{t.title}</h3>
                      <p className="text-violet-100 text-sm mt-1">{t.destination} &middot; {t.duration_days} days</p>
                      <div className="flex items-center gap-3 mt-3 text-xs text-violet-200">
                        <span>{t.clone_count} clones</span><span>{renderStars(t.rating)}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Filters */}
            <div className="flex flex-wrap gap-3 mb-6">
              <input type="text" placeholder="Filter by destination..." value={destination} onChange={e => setDestination(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchTemplates()}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm" />
              <select value={style} onChange={e => setStyle(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm">
                {STYLES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm">
                {SORT_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>

            {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
            templates.length === 0 ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">🗺️</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No templates found</h3>
                <p className="text-gray-500">Try different filters or create the first template for this destination!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {templates.map(t => (
                  <div key={t.id} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow flex flex-col">
                    <button onClick={() => viewTemplate(t.id)} className="text-left px-5 py-4 border-b border-gray-100 dark:border-gray-700 w-full">
                      <div className="flex items-center gap-2 mb-1">
                        <span>{STYLE_EMOJIS[t.style] || '✈️'}</span>
                        <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded-full">{t.style}</span>
                        {t.is_verified && <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 px-2 py-0.5 rounded-full">Verified</span>}
                      </div>
                      <h3 className="font-bold text-gray-900 dark:text-white line-clamp-1">{t.title}</h3>
                      <p className="text-sm text-gray-500 mt-0.5">{t.destination} &middot; {t.duration_days} days &middot; ${t.estimated_budget}</p>
                    </button>
                    <div className="px-5 py-3 flex items-center gap-1.5 text-xs border-b border-gray-100 dark:border-gray-700 flex-wrap">
                      <button
                        onClick={e => { e.stopPropagation(); reactTemplate(t, 'like'); }}
                        className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                          t.my_reaction === 'like'
                            ? 'bg-pink-500 text-white'
                            : 'bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 hover:bg-pink-100'
                        }`}
                        aria-pressed={t.my_reaction === 'like'}
                        aria-label="Like"
                      >👍 {t.likes_count}</button>
                      <button
                        onClick={e => { e.stopPropagation(); reactTemplate(t, 'dislike'); }}
                        className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                          t.my_reaction === 'dislike'
                            ? 'bg-gray-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                        }`}
                        aria-pressed={t.my_reaction === 'dislike'}
                        aria-label="Dislike"
                      >👎 {t.dislikes_count ?? 0}</button>
                      <button
                        onClick={e => { e.stopPropagation(); viewTemplate(t.id); }}
                        className="flex items-center gap-1 px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200"
                        aria-label="Comments"
                      >💬 {t.comments_count ?? 0}</button>
                      <button
                        onClick={e => { e.stopPropagation(); shareTemplate(t); }}
                        className="flex items-center gap-1 px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100"
                        aria-label="Share"
                      >🔗</button>
                      <span className="text-yellow-500 ml-auto">{renderStars(t.rating)}</span>
                    </div>
                    <div className="px-5 py-2 flex items-center justify-between text-xs text-gray-400">
                      <span>{t.clone_count} clones</span>
                      <span>{t.views_count ?? 0} views</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Create */}
        {tab === 'create' && (
          <div className="max-w-xl mx-auto">
            {!isAuthenticated ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">🔒</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Sign in to create templates</h3>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">AI-Generate a Trip Template</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
                    <input type="text" value={genForm.destination} onChange={e => setGenForm(f => ({ ...f, destination: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="e.g. Bali, Indonesia" />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Days</label>
                      <input type="number" min={1} max={30} value={genForm.duration_days} onChange={e => setGenForm(f => ({ ...f, duration_days: parseInt(e.target.value) || 1 }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Style</label>
                      <select value={genForm.style} onChange={e => setGenForm(f => ({ ...f, style: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                        {STYLES.filter(s => s.value).map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Budget ($)</label>
                      <input type="number" min={0} value={genForm.budget} onChange={e => setGenForm(f => ({ ...f, budget: parseFloat(e.target.value) || 0 }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                    </div>
                  </div>
                  <button onClick={generateTemplate} disabled={generating}
                    className="w-full py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl font-semibold text-lg hover:from-violet-700 hover:to-purple-700 shadow-lg disabled:opacity-50">
                    {generating ? 'Generating...' : 'Generate Trip Template'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* My Templates */}
        {tab === 'my-templates' && (
          loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
          myTemplates.length === 0 ? (
            <div className="text-center py-16"><div className="text-5xl mb-4">📋</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No templates yet</h3>
              <button onClick={() => setTab('create')} className="mt-4 px-6 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700">Create Template</button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {myTemplates.map(t => (
                <div key={t.id} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
                  <button onClick={() => viewTemplate(t.id)} className="text-left w-full">
                    <span className="text-2xl">{STYLE_EMOJIS[t.style] || '✈️'}</span>
                    <h3 className="font-bold text-gray-900 dark:text-white mt-2">{t.title}</h3>
                    <p className="text-sm text-gray-500 mt-1">{t.destination} &middot; {t.duration_days} days</p>
                  </button>
                  <div className="flex items-center gap-1.5 mt-3 text-xs flex-wrap">
                    <button
                      onClick={e => { e.stopPropagation(); reactTemplate(t, 'like'); }}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                        t.my_reaction === 'like'
                          ? 'bg-pink-500 text-white'
                          : 'bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 hover:bg-pink-100'
                      }`}
                      aria-pressed={t.my_reaction === 'like'}
                    >👍 {t.likes_count}</button>
                    <button
                      onClick={e => { e.stopPropagation(); reactTemplate(t, 'dislike'); }}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                        t.my_reaction === 'dislike'
                          ? 'bg-gray-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                      }`}
                      aria-pressed={t.my_reaction === 'dislike'}
                    >👎 {t.dislikes_count ?? 0}</button>
                    <button
                      onClick={e => { e.stopPropagation(); viewTemplate(t.id); }}
                      className="flex items-center gap-1 px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200"
                    >💬 {t.comments_count ?? 0}</button>
                    <button
                      onClick={e => { e.stopPropagation(); shareTemplate(t); }}
                      className="flex items-center gap-1 px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100"
                    >🔗</button>
                    <span className="text-gray-400 ml-auto">{t.clone_count} clones</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
