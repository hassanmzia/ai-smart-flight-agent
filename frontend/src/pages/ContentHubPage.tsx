import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface ContentComment {
  id: number;
  user: string;
  user_id?: number | string;
  content: string;
  created_at: string;
}

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
  likes_count?: number;
  dislikes_count?: number;
  comments_count?: number;
  views_count: number;
  user_name?: string;
  user_id?: number | string;
  my_vote?: 'up' | 'down' | null;
  my_reaction?: 'like' | 'dislike' | null;
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
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuth();
  const currentUserId = user?.id;
  const [tab, setTab] = useState<Tab>('explore');
  const [content, setContent] = useState<ContentItemData[]>([]);
  const [myContent, setMyContent] = useState<ContentItemData[]>([]);
  const [trending, setTrending] = useState<ContentItemData[]>([]);
  const [loading, setLoading] = useState(false);
  const [destination, setDestination] = useState('');
  const [contentType, setContentType] = useState('');
  const [sortBy, setSortBy] = useState('popular');
  const [activeComments, setActiveComments] = useState<number | null>(null);
  const [comments, setComments] = useState<ContentComment[]>([]);
  const [commentText, setCommentText] = useState('');

  const [form, setForm] = useState({
    destination: '', content_type: 'tip', title: '', description: '', body: '', media_url: '',
    tags: '',
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setDestination(dest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

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

  const applyReactionC = (it: ContentItemData, reaction: 'like' | 'dislike'): ContentItemData => {
    const current = it.my_reaction ?? (it.my_vote === 'up' ? 'like' : it.my_vote === 'down' ? 'dislike' : null);
    let likes = it.likes_count ?? it.upvotes ?? 0;
    let dislikes = it.dislikes_count ?? it.downvotes ?? 0;
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
      ...it,
      my_reaction: next,
      my_vote: next === 'like' ? 'up' : next === 'dislike' ? 'down' : null,
      likes_count: Math.max(0, likes),
      dislikes_count: Math.max(0, dislikes),
      upvotes: Math.max(0, likes),
      downvotes: Math.max(0, dislikes),
    };
  };

  const patchLists = (id: number, patch: Partial<ContentItemData>) => {
    setContent(prev => prev.map(x => x.id === id ? { ...x, ...patch } : x));
    setTrending(prev => prev.map(x => x.id === id ? { ...x, ...patch } : x));
    setMyContent(prev => prev.map(x => x.id === id ? { ...x, ...patch } : x));
  };

  const reactContent = async (item: ContentItemData, reaction: 'like' | 'dislike') => {
    if (!isAuthenticated) { toast.error('Sign in to react'); return; }
    const updated = applyReactionC(item, reaction);
    patchLists(item.id, updated);
    try {
      const res = await api.post('/api/agents/content/vote', {
        content_id: item.id, reaction,
      });
      if (res.data?.success) {
        const likes = res.data.likes_count ?? res.data.upvotes;
        const dislikes = res.data.dislikes_count ?? res.data.downvotes;
        patchLists(item.id, {
          my_reaction: res.data.my_reaction ?? null,
          my_vote: res.data.my_vote ?? null,
          likes_count: likes,
          dislikes_count: dislikes,
          upvotes: likes,
          downvotes: dislikes,
        });
      }
    } catch {
      patchLists(item.id, item);
      toast.error('Failed to react');
    }
  };

  const loadComments = useCallback(async (contentId: number) => {
    try {
      const res = await api.get('/api/agents/content/comments', { params: { content_id: contentId } });
      const items = res.data?.comments;
      setComments(Array.isArray(items) ? items : []);
    } catch { setComments([]); }
  }, []);

  const toggleComments = (item: ContentItemData) => {
    if (activeComments === item.id) {
      setActiveComments(null);
      setComments([]);
    } else {
      setActiveComments(item.id);
      loadComments(item.id);
    }
  };

  const addContentComment = async (item: ContentItemData) => {
    if (!commentText.trim()) return;
    if (!isAuthenticated) { toast.error('Sign in to comment'); return; }
    try {
      const res = await api.post('/api/agents/content/comments', {
        content_id: item.id, content: commentText,
      });
      if (res.data?.success) {
        setComments(prev => [res.data.comment, ...prev]);
        patchLists(item.id, {
          comments_count: res.data.comments_count ?? ((item.comments_count ?? 0) + 1),
        });
        setCommentText('');
        toast.success('Comment posted');
      } else {
        toast.error(res.data?.error || 'Comment failed');
      }
    } catch { toast.error('Failed to add comment'); }
  };

  const deleteContentComment = async (commentId: number, item: ContentItemData) => {
    try {
      const res = await api.delete(`/api/agents/content/comments/${commentId}`);
      if (res.data?.success) {
        setComments(prev => prev.filter(c => c.id !== commentId));
        patchLists(item.id, {
          comments_count: res.data.comments_count ?? Math.max(0, (item.comments_count ?? 1) - 1),
        });
        toast.success('Comment deleted');
      } else {
        toast.error(res.data?.error || 'Delete failed');
      }
    } catch { toast.error('Failed to delete'); }
  };

  const shareContent = async (item: ContentItemData) => {
    const url = `${window.location.origin}/content-hub?destination=${encodeURIComponent(item.destination)}&item=${item.id}`;
    const shareData = {
      title: item.title,
      text: `${item.title} – ${item.destination}`,
      url,
    };
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

  const renderCard = (item: ContentItemData) => {
    const likes = item.likes_count ?? item.upvotes ?? 0;
    const dislikes = item.dislikes_count ?? item.downvotes ?? 0;
    const commentsCount = item.comments_count ?? 0;
    const myReaction = item.my_reaction ?? (item.my_vote === 'up' ? 'like' : item.my_vote === 'down' ? 'dislike' : null);
    const isOpen = activeComments === item.id;
    return (
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
          <div className="flex items-center gap-1.5 mt-4 pt-3 border-t border-gray-100 dark:border-gray-700 flex-wrap">
            <button
              onClick={() => reactContent(item, 'like')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-sm transition ${
                myReaction === 'like'
                  ? 'bg-pink-500 text-white'
                  : 'bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 hover:bg-pink-100'
              }`}
              aria-pressed={myReaction === 'like'}
              aria-label="Like"
            >👍 {likes}</button>
            <button
              onClick={() => reactContent(item, 'dislike')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-sm transition ${
                myReaction === 'dislike'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
              aria-pressed={myReaction === 'dislike'}
              aria-label="Dislike"
            >👎 {dislikes}</button>
            <button
              onClick={() => toggleComments(item)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-sm transition ${
                isOpen
                  ? 'bg-teal-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
              }`}
              aria-label="Comments"
            >💬 {commentsCount}</button>
            <button
              onClick={() => shareContent(item)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-md text-sm bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100"
              aria-label="Share"
            >🔗</button>
            <div className="ml-auto text-xs text-gray-400">
              <span>{item.views_count} views</span>
              {item.user_name && <span className="ml-2">by {item.user_name}</span>}
            </div>
          </div>
          {isOpen && (
            <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700">
              {comments.length === 0 && (
                <p className="text-xs text-gray-400">No comments yet — be the first!</p>
              )}
              {comments.map(c => {
                const isOwn = currentUserId != null && String(c.user_id) === String(currentUserId);
                return (
                  <div key={c.id} className="py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-0.5">
                      <span className="font-medium text-gray-700 dark:text-gray-300">{c.user}</span>
                      <span>{new Date(c.created_at).toLocaleDateString()}</span>
                      {isOwn && (
                        <button
                          onClick={() => deleteContentComment(c.id, item)}
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
                    onKeyDown={e => { if (e.key === 'Enter') addContentComment(item); }}
                    placeholder="Add a comment..."
                    className="flex-1 px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                  />
                  <button
                    onClick={() => addContentComment(item)}
                    className="px-3 py-1.5 bg-teal-500 text-white rounded-md text-sm hover:bg-teal-600"
                  >Post</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

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
              {myContent.map(item => {
                const likes = item.likes_count ?? item.upvotes ?? 0;
                const dislikes = item.dislikes_count ?? item.downvotes ?? 0;
                const commentsCount = item.comments_count ?? 0;
                return (
                  <div key={item.id} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${TYPE_COLORS[item.content_type] || ''}`}>{item.content_type}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            item.status === 'approved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                            item.status === 'rejected' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                            'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                          }`}>{item.status}</span>
                        </div>
                        <h3 className="font-bold text-gray-900 dark:text-white">{item.title}</h3>
                        <p className="text-xs text-gray-500 mt-0.5">{item.destination}</p>
                      </div>
                      <span className="text-xs text-gray-400 flex-shrink-0">{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-3 text-xs flex-wrap">
                      <span className="px-2 py-1 rounded-md bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400">👍 {likes}</span>
                      <span className="px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">👎 {dislikes}</span>
                      <span className="px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">💬 {commentsCount}</span>
                      <button
                        onClick={() => shareContent(item)}
                        className="px-2 py-1 rounded-md bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100"
                      >🔗 Share</button>
                      <span className="text-gray-400 ml-auto">{item.views_count} views</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </div>
    </div>
  );
}
