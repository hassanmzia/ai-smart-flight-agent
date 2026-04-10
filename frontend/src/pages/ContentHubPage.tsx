import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface ContentItemData {
  id: number;
  title: string;
  description: string;
  destination: string;
  content_type: string;
  media_url: string;
  body: string;
  tags: string[];
  status: string;
  upvotes: number;
  downvotes: number;
  views_count: number;
  user_name?: string;
  created_at: string;
}

const CONTENT_TYPES = [
  { value: '', label: 'All Types', icon: '📋' },
  { value: 'photo', label: 'Photos', icon: '📸' },
  { value: 'story', label: 'Stories', icon: '📖' },
  { value: 'tip', label: 'Tips', icon: '💡' },
  { value: 'video', label: 'Videos', icon: '🎥' },
  { value: 'audio', label: 'Audio', icon: '🎧' },
];

const TYPE_COLORS: Record<string, string> = {
  photo: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  story: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
  tip: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  video: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  audio: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
};

type Tab = 'explore' | 'submit' | 'my-content' | 'trending';

export default function ContentHubPage() {
  const { isAuthenticated } = useAuth();
  const [tab, setTab] = useState<Tab>('explore');
  const [content, setContent] = useState<ContentItemData[]>([]);
  const [myContent, setMyContent] = useState<ContentItemData[]>([]);
  const [trending, setTrending] = useState<ContentItemData[]>([]);
  const [loading, setLoading] = useState(false);
  const [destination, setDestination] = useState('');
  const [contentType, setContentType] = useState('');
  const [sortBy, setSortBy] = useState('popular');

  const [form, setForm] = useState({
    destination: '', content_type: 'tip', title: '', description: '', body: '', media_url: '',
    tags: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchContent = useCallback(async () => {
    if (!destination.trim()) return;
    setLoading(true);
    try {
      const params: Record<string, string> = { destination, sort_by: sortBy };
      if (contentType) params.type = contentType;
      const res = await api.get('/api/agents/content/destination', { params });
      const items = res.data?.content || res.data?.items || res.data;
      setContent(Array.isArray(items) ? items : []);
    } catch { setContent([]); }
    finally { setLoading(false); }
  }, [destination, contentType, sortBy]);

  const fetchTrending = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/agents/content/trending');
      const items = res.data?.content || res.data?.items || res.data;
      setTrending(Array.isArray(items) ? items : []);
    } catch { setTrending([]); }
    finally { setLoading(false); }
  }, []);

  const fetchMyContent = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/api/agents/content/mine');
      const items = res.data?.content || res.data?.items || res.data;
      setMyContent(Array.isArray(items) ? items : []);
    } catch { setMyContent([]); }
    finally { setLoading(false); }
  }, [isAuthenticated]);

  useEffect(() => {
    if (tab === 'trending') fetchTrending();
    else if (tab === 'my-content') fetchMyContent();
  }, [tab, fetchTrending, fetchMyContent]);

  const submitContent = async () => {
    if (!form.destination || !form.title) { toast.error('Destination and title are required'); return; }
    setSubmitting(true);
    try {
      const res = await api.post('/api/agents/content/submit', {
        ...form,
        tags: form.tags.split(',').map(t => t.trim()).filter(Boolean),
      });
      if (res.data?.success) {
        const statusMsg = res.data.status === 'approved' ? 'Content published!' : 'Content submitted for review!';
        toast.success(statusMsg);
        setForm({ destination: '', content_type: 'tip', title: '', description: '', body: '', media_url: '', tags: '' });
        setTab('my-content');
        fetchMyContent();
      }
    } catch { toast.error('Submission failed'); }
    finally { setSubmitting(false); }
  };

  const voteContent = async (id: number, vote: 'up' | 'down') => {
    try {
      await api.post('/api/agents/content/vote', { content_id: id, vote });
      toast.success(vote === 'up' ? 'Upvoted!' : 'Downvoted');
      if (tab === 'explore') fetchContent();
      else if (tab === 'trending') fetchTrending();
    } catch { toast.error('Sign in to vote'); }
  };

  const renderCard = (item: ContentItemData) => (
    <div key={item.id} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="p-5">
        <div className="flex items-center gap-2 mb-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[item.content_type] || 'bg-gray-100 text-gray-600'}`}>
            {item.content_type}
          </span>
          <span className="text-xs text-gray-400">{item.destination}</span>
        </div>
        <h3 className="font-bold text-gray-900 dark:text-white">{item.title}</h3>
        {item.description && <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">{item.description}</p>}
        {item.body && <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-3">{item.body}</p>}
        {item.media_url && (
          <div className="mt-3 bg-gray-100 dark:bg-gray-700 rounded-lg px-3 py-2 text-xs text-gray-500 truncate">{item.media_url}</div>
        )}
        {item.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {item.tags.slice(0, 5).map((tag, i) => (
              <span key={i} className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-full">#{tag}</span>
            ))}
          </div>
        )}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <button onClick={() => voteContent(item.id, 'up')} className="flex items-center gap-1 text-sm text-green-500 hover:text-green-700">
              &#9650; {item.upvotes}
            </button>
            <button onClick={() => voteContent(item.id, 'down')} className="flex items-center gap-1 text-sm text-red-400 hover:text-red-600">
              &#9660; {item.downvotes}
            </button>
          </div>
          <div className="text-xs text-gray-400">
            <span>{item.views_count} views</span>
            {item.user_name && <span className="ml-2">by {item.user_name}</span>}
          </div>
        </div>
      </div>
    </div>
  );

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'explore', label: 'Explore', icon: '🔍' },
    { id: 'trending', label: 'Trending', icon: '🔥' },
    { id: 'submit', label: 'Submit', icon: '➕' },
    { id: 'my-content', label: 'My Content', icon: '📁' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-cyan-600 via-teal-600 to-emerald-600 dark:from-cyan-800 dark:via-teal-800 dark:to-emerald-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2">Content Hub</h1>
          <p className="text-teal-100 text-lg">Community photos, stories, tips & more</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-teal-600 text-white shadow-lg' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
              }`}>
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {/* Explore */}
        {tab === 'explore' && (
          <div>
            <div className="flex flex-wrap gap-3 mb-6">
              <input type="text" placeholder="Search destination..." value={destination}
                onChange={e => setDestination(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchContent()}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm flex-1 min-w-[200px]" />
              <select value={contentType} onChange={e => setContentType(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm">
                {CONTENT_TYPES.map(c => <option key={c.value} value={c.value}>{c.icon} {c.label}</option>)}
              </select>
              <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm">
                <option value="popular">Most Popular</option>
                <option value="newest">Newest</option>
                <option value="most_viewed">Most Viewed</option>
              </select>
              <button onClick={fetchContent} className="px-5 py-2 bg-teal-600 text-white rounded-lg text-sm hover:bg-teal-700">Search</button>
            </div>

            {loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
            !destination.trim() ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">🔍</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Search a destination</h3>
                <p className="text-gray-500">Enter a city or country to discover community content</p>
              </div>
            ) : content.length === 0 ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">📭</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No content found</h3>
                <p className="text-gray-500">Be the first to share content about {destination}!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {content.map(renderCard)}
              </div>
            )}
          </div>
        )}

        {/* Trending */}
        {tab === 'trending' && (
          loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
          trending.length === 0 ? (
            <div className="text-center py-16"><div className="text-5xl mb-4">🔥</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No trending content yet</h3>
              <p className="text-gray-500">Content with the most upvotes this week appears here</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {trending.map(renderCard)}
            </div>
          )
        )}

        {/* Submit */}
        {tab === 'submit' && (
          <div className="max-w-xl mx-auto">
            {!isAuthenticated ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">🔒</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Sign in to submit content</h3>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Share Content</h2>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
                      <input type="text" value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="e.g. Barcelona" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type *</label>
                      <select value={form.content_type} onChange={e => setForm(f => ({ ...f, content_type: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                        {CONTENT_TYPES.filter(c => c.value).map(c => <option key={c.value} value={c.value}>{c.icon} {c.label}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title *</label>
                    <input type="text" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="Give your content a title" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                    <input type="text" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="Brief description" />
                  </div>
                  {(form.content_type === 'photo' || form.content_type === 'video' || form.content_type === 'audio') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Media URL</label>
                      <input type="url" value={form.media_url} onChange={e => setForm(f => ({ ...f, media_url: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="https://..." />
                    </div>
                  )}
                  {(form.content_type === 'story' || form.content_type === 'tip') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Content</label>
                      <textarea value={form.body} onChange={e => setForm(f => ({ ...f, body: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" rows={5}
                        placeholder="Share your experience..." />
                    </div>
                  )}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tags (comma-separated)</label>
                    <input type="text" value={form.tags} onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="food, culture, hidden gem" />
                  </div>
                  <button onClick={submitContent} disabled={submitting}
                    className="w-full py-3 bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-xl font-semibold text-lg hover:from-teal-700 hover:to-emerald-700 shadow-lg disabled:opacity-50">
                    {submitting ? 'Submitting...' : 'Submit Content'}
                  </button>
                  <p className="text-xs text-gray-400 text-center">Content is reviewed by AI before publishing</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* My Content */}
        {tab === 'my-content' && (
          loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
          myContent.length === 0 ? (
            <div className="text-center py-16"><div className="text-5xl mb-4">📁</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No content yet</h3>
              <button onClick={() => setTab('submit')} className="mt-4 px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700">Submit Content</button>
            </div>
          ) : (
            <div className="space-y-4">
              {myContent.map(item => (
                <div key={item.id} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[item.content_type] || ''}`}>{item.content_type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        item.status === 'approved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                        item.status === 'rejected' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                      }`}>{item.status}</span>
                    </div>
                    <h3 className="font-bold text-gray-900 dark:text-white">{item.title}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">{item.destination} &middot; &#9650; {item.upvotes} &middot; {item.views_count} views</p>
                  </div>
                  <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}
