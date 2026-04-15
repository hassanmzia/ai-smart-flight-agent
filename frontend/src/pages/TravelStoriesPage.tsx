import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface StoryCard {
  day: number;
  title: string;
  content: string;
  mood: string;
  image_url?: string;
}

interface StoryComment {
  id: number;
  user: string;
  user_id?: number | string;
  user_name?: string;
  content: string;
  created_at: string;
}

interface Story {
  id: number;
  title: string;
  content: string;
  format: string;
  status: string;
  destination: string;
  cover_image_url: string;
  tags: string[];
  story_cards: StoryCard[];
  share_token: string;
  views_count: number;
  likes_count: number;
  dislikes_count?: number;
  comments_count?: number;
  shares_count: number;
  is_public: boolean;
  my_reaction?: 'like' | 'dislike' | null;
  created_at: string;
  user_name?: string;
  comments?: StoryComment[];
}

const FORMAT_OPTIONS = [
  { value: 'journal', label: 'Daily Journal', icon: '📓' },
  { value: 'instagram', label: 'Instagram Story', icon: '📸' },
  { value: 'blog', label: 'Blog Post', icon: '✍️' },
  { value: 'social', label: 'Social Post', icon: '📱' },
  { value: 'thread', label: 'Thread', icon: '🧵' },
];

type Tab = 'explore' | 'create' | 'my-stories';

export default function TravelStoriesPage() {
  const [searchParams] = useSearchParams();
  const { isAuthenticated, user } = useAuth();
  const currentUserId = user?.id;
  const [tab, setTab] = useState<Tab>('explore');
  const [stories, setStories] = useState<Story[]>([]);
  const [myStories, setMyStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedStory, setSelectedStory] = useState<Story | null>(null);
  const [commentText, setCommentText] = useState('');

  // Create form
  const [form, setForm] = useState({
    destination: '', trip_days: 3, format: 'journal',
    highlights: '',
  });
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const dest = searchParams.get('destination');
    if (dest) setForm((prev) => ({ ...prev, destination: dest }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const fetchPublicStories = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/agents/stories/public');
      const items = res.data?.stories || res.data?.items || res.data?.results;
      setStories(Array.isArray(items) ? items : []);
    } catch { setStories([]); }
    finally { setLoading(false); }
  }, []);

  const fetchMyStories = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const res = await api.get('/api/agents/stories/mine');
      const items = res.data?.stories || res.data?.items;
      setMyStories(Array.isArray(items) ? items : []);
    } catch { setMyStories([]); }
    finally { setLoading(false); }
  }, [isAuthenticated]);

  useEffect(() => {
    if (tab === 'explore') fetchPublicStories();
    else if (tab === 'my-stories') fetchMyStories();
  }, [tab, fetchPublicStories, fetchMyStories]);

  const generateStory = async () => {
    if (!form.destination) { toast.error('Enter a destination'); return; }
    setGenerating(true);
    try {
      const res = await api.post('/api/agents/stories/generate', {
        destination: form.destination,
        trip_days: form.trip_days,
        format: form.format,
        highlights: form.highlights.split(',').map(h => h.trim()).filter(Boolean),
      }, { timeout: 90000 });
      if (res.data?.success) {
        toast.success('Story generated!');
        setTab('my-stories');
        fetchMyStories();
      } else {
        toast.error(res.data?.error || 'Generation failed');
      }
    } catch { toast.error('Failed to generate story'); }
    finally { setGenerating(false); }
  };

  const publishStory = async (storyId: number) => {
    try {
      await api.post('/api/agents/stories/publish', { story_id: storyId });
      toast.success('Story published!');
      fetchMyStories();
    } catch { toast.error('Failed to publish'); }
  };

  const applyReaction = (s: Story, reaction: 'like' | 'dislike'): Story => {
    const current = s.my_reaction;
    let likes = s.likes_count;
    let dislikes = s.dislikes_count ?? 0;
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
      ...s,
      my_reaction: next,
      likes_count: Math.max(0, likes),
      dislikes_count: Math.max(0, dislikes),
    };
  };

  const reactStory = async (story: Story, reaction: 'like' | 'dislike') => {
    if (!isAuthenticated) { toast.error('Sign in to react'); return; }
    const updated = applyReaction(story, reaction);
    setStories(prev => prev.map(x => x.id === story.id ? { ...x, ...updated } : x));
    setMyStories(prev => prev.map(x => x.id === story.id ? { ...x, ...updated } : x));
    if (selectedStory?.id === story.id) setSelectedStory({ ...selectedStory, ...updated });
    try {
      const res = await api.post('/api/agents/stories/react', {
        story_id: story.id, reaction,
      });
      if (res.data?.success) {
        const patched = {
          my_reaction: res.data.my_reaction ?? null,
          likes_count: res.data.likes_count,
          dislikes_count: res.data.dislikes_count,
        };
        setStories(prev => prev.map(x => x.id === story.id ? { ...x, ...patched } : x));
        setMyStories(prev => prev.map(x => x.id === story.id ? { ...x, ...patched } : x));
        if (selectedStory?.id === story.id) setSelectedStory(s => s ? { ...s, ...patched } : s);
      }
    } catch {
      // Rollback
      setStories(prev => prev.map(x => x.id === story.id ? story : x));
      setMyStories(prev => prev.map(x => x.id === story.id ? story : x));
      if (selectedStory?.id === story.id) setSelectedStory(story);
      toast.error('Failed to react');
    }
  };

  const viewStory = async (shareToken: string) => {
    try {
      const res = await api.get(`/api/agents/stories/${shareToken}`);
      setSelectedStory(res.data?.story || null);
    } catch { toast.error('Story not found'); }
  };

  const addComment = async () => {
    if (!selectedStory || !commentText.trim()) return;
    if (!isAuthenticated) { toast.error('Sign in to comment'); return; }
    try {
      const res = await api.post('/api/agents/stories/comment', {
        story_id: selectedStory.id,
        content: commentText,
      });
      if (res.data?.success) {
        const newComment = res.data.comment;
        setSelectedStory(s => s ? {
          ...s,
          comments_count: res.data.comments_count ?? (s.comments_count ?? 0) + 1,
          comments: [newComment, ...(s.comments || [])],
        } : s);
        setCommentText('');
        toast.success('Comment posted');
      } else {
        toast.error(res.data?.error || 'Comment failed');
      }
    } catch { toast.error('Failed to add comment'); }
  };

  const deleteComment = async (commentId: number) => {
    if (!selectedStory) return;
    try {
      const res = await api.delete(`/api/agents/stories/comments/${commentId}`);
      if (res.data?.success) {
        setSelectedStory(s => s ? {
          ...s,
          comments_count: res.data.comments_count ?? Math.max(0, (s.comments_count ?? 1) - 1),
          comments: (s.comments || []).filter(c => c.id !== commentId),
        } : s);
        toast.success('Comment deleted');
      } else {
        toast.error(res.data?.error || 'Delete failed');
      }
    } catch { toast.error('Failed to delete'); }
  };

  const shareStory = async (story: Story) => {
    const url = `${window.location.origin}/stories/${story.share_token}`;
    const shareData = { title: story.title, text: `${story.title} – a travel story`, url };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(url);
        toast.success('Share link copied!');
      }
    } catch (err) {
      // Silently ignore user cancellation of Web Share
      const msg = (err as { name?: string })?.name;
      if (msg !== 'AbortError') {
        try {
          await navigator.clipboard.writeText(url);
          toast.success('Share link copied!');
        } catch { toast.error('Failed to share'); }
      }
    }
  };

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'explore', label: 'Explore Stories', icon: '🌍' },
    { id: 'create', label: 'Create Story', icon: '✨' },
    { id: 'my-stories', label: 'My Stories', icon: '📚' },
  ];

  // Story detail modal
  if (selectedStory) {
    const s = selectedStory;
    const reactionLiked = s.my_reaction === 'like';
    const reactionDisliked = s.my_reaction === 'dislike';
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <button onClick={() => setSelectedStory(null)} className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-6">&larr; Back to stories</button>
          <article className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="bg-gradient-to-r from-rose-500 to-pink-500 px-6 py-5">
              <h1 className="text-2xl font-bold text-white">{s.title}</h1>
              <div className="flex items-center gap-3 mt-2 text-rose-100 text-sm">
                <span>{s.destination}</span>
                <span>&#9679;</span>
                <span>{s.format}</span>
                <span>&#9679;</span>
                <span>{s.user_name || 'Traveler'}</span>
              </div>
            </div>
            <div className="p-6">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">{s.content}</p>

              {s.story_cards?.length > 0 && (
                <div className="mt-8 space-y-4">
                  <h3 className="font-bold text-gray-900 dark:text-white">Story Cards</h3>
                  {s.story_cards.map((card, i) => (
                    <div key={i} className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-750 rounded-xl p-4 border border-gray-200 dark:border-gray-600">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{card.mood || '📍'}</span>
                        <span className="font-semibold text-gray-900 dark:text-white">Day {card.day}: {card.title}</span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-300">{card.content}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Social bar */}
              <div className="flex items-center gap-3 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700 flex-wrap">
                <button
                  onClick={() => reactStory(s, 'like')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    reactionLiked
                      ? 'bg-rose-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-rose-100 dark:hover:bg-rose-900/20'
                  }`}
                  aria-pressed={reactionLiked}
                >
                  <span>👍</span>
                  <span>{s.likes_count}</span>
                </button>
                <button
                  onClick={() => reactStory(s, 'dislike')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                    reactionDisliked
                      ? 'bg-gray-600 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  aria-pressed={reactionDisliked}
                >
                  <span>👎</span>
                  <span>{s.dislikes_count ?? 0}</span>
                </button>
                <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-gray-500 bg-gray-100 dark:bg-gray-700">
                  <span>💬</span>
                  <span>{s.comments_count ?? s.comments?.length ?? 0}</span>
                </span>
                <button
                  onClick={() => shareStory(s)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50"
                >
                  <span>🔗</span>
                  <span>Share</span>
                </button>
                <span className="text-xs text-gray-400 ml-auto">{s.views_count} views</span>
              </div>

              {/* Comments */}
              <div className="mt-6">
                <h3 className="font-bold text-gray-900 dark:text-white mb-3">Comments</h3>
                {(!s.comments || s.comments.length === 0) && (
                  <p className="text-sm text-gray-400">No comments yet — be the first!</p>
                )}
                {s.comments?.map((c) => {
                  const isOwn = currentUserId != null && String(c.user_id) === String(currentUserId);
                  return (
                    <div key={c.id} className="py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                      <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                        <span className="font-medium text-gray-700 dark:text-gray-300">{c.user || c.user_name}</span>
                        <span>{new Date(c.created_at).toLocaleDateString()}</span>
                        {isOwn && (
                          <button
                            onClick={() => deleteComment(c.id)}
                            className="ml-auto text-red-400 hover:text-red-600 text-xs"
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
                      onKeyDown={e => { if (e.key === 'Enter') addComment(); }}
                      placeholder="Add a comment..."
                      className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                    />
                    <button onClick={addComment} className="px-4 py-2 bg-rose-500 text-white rounded-lg text-sm hover:bg-rose-600">Post</button>
                  </div>
                )}
              </div>
            </div>
          </article>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero */}
      <div className="bg-gradient-to-br from-rose-600 via-pink-600 to-fuchsia-600 dark:from-rose-800 dark:via-pink-800 dark:to-fuchsia-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <h1 className="text-2xl md:text-3xl font-extrabold text-white mb-2">AI Travel Stories</h1>
          <p className="text-pink-100 text-lg">Generate shareable travel narratives from your trips</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-rose-600 text-white shadow-lg' : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
              }`}>
              <span>{t.icon}</span> {t.label}
            </button>
          ))}
        </div>

        {/* Explore */}
        {tab === 'explore' && (
          loading ? <div className="text-center py-12 text-gray-500">Loading stories...</div> :
          stories.length === 0 ? (
            <div className="text-center py-16"><div className="text-5xl mb-4">📖</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No stories yet</h3>
              <p className="text-gray-500">Be the first to create and share a travel story!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {stories.map(story => (
                <div key={story.id} className="flex flex-col bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow">
                  <button onClick={() => viewStory(story.share_token)} className="text-left">
                    <div className="bg-gradient-to-r from-rose-400 to-pink-400 px-5 py-4">
                      <span className="text-xs bg-white/20 text-white px-2 py-0.5 rounded-full">{story.format}</span>
                      <h3 className="font-bold text-white text-lg mt-2 line-clamp-2">{story.title}</h3>
                    </div>
                    <div className="px-5 pt-4">
                      <p className="text-sm text-gray-500 dark:text-gray-400">{story.destination}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-3">{story.content?.substring(0, 150)}...</p>
                    </div>
                  </button>
                  {/* Social bar */}
                  <div className="mt-auto flex items-center gap-2 px-5 py-3 border-t border-gray-100 dark:border-gray-700 text-xs">
                    <button
                      onClick={(e) => { e.stopPropagation(); reactStory(story, 'like'); }}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                        story.my_reaction === 'like'
                          ? 'bg-rose-500 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-rose-100 dark:hover:bg-rose-900/20'
                      }`}
                      aria-label="Like"
                    >
                      <span>👍</span><span>{story.likes_count}</span>
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); reactStory(story, 'dislike'); }}
                      className={`flex items-center gap-1 px-2 py-1 rounded-md transition ${
                        story.my_reaction === 'dislike'
                          ? 'bg-gray-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                      aria-label="Dislike"
                    >
                      <span>👎</span><span>{story.dislikes_count ?? 0}</span>
                    </button>
                    <span className="flex items-center gap-1 px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-500">
                      💬 {story.comments_count ?? 0}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); shareStory(story); }}
                      className="ml-auto flex items-center gap-1 px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50"
                      aria-label="Share"
                    >
                      🔗 Share
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Create */}
        {tab === 'create' && (
          <div className="max-w-xl mx-auto">
            {!isAuthenticated ? (
              <div className="text-center py-16"><div className="text-5xl mb-4">🔒</div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Sign in to create stories</h3>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Generate a Travel Story</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Destination *</label>
                    <input type="text" value={form.destination} onChange={e => setForm(f => ({ ...f, destination: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" placeholder="e.g. Tokyo, Japan" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Trip Days</label>
                      <input type="number" min={1} max={30} value={form.trip_days} onChange={e => setForm(f => ({ ...f, trip_days: parseInt(e.target.value) || 1 }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Format</label>
                      <select value={form.format} onChange={e => setForm(f => ({ ...f, format: e.target.value }))}
                        className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                        {FORMAT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.icon} {o.label}</option>)}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Trip Highlights (comma-separated)</label>
                    <textarea value={form.highlights} onChange={e => setForm(f => ({ ...f, highlights: e.target.value }))}
                      className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white" rows={3}
                      placeholder="Shibuya crossing, sushi at Tsukiji, Mt. Fuji sunrise..." />
                  </div>
                  <button onClick={generateStory} disabled={generating}
                    className="w-full py-3 bg-gradient-to-r from-rose-600 to-pink-600 text-white rounded-xl font-semibold text-lg hover:from-rose-700 hover:to-pink-700 shadow-lg disabled:opacity-50">
                    {generating ? 'Generating...' : 'Generate Story'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* My Stories */}
        {tab === 'my-stories' && (
          loading ? <div className="text-center py-12 text-gray-500">Loading...</div> :
          myStories.length === 0 ? (
            <div className="text-center py-16"><div className="text-5xl mb-4">✨</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">No stories yet</h3>
              <p className="text-gray-500">Generate your first AI travel story!</p>
              <button onClick={() => setTab('create')} className="mt-4 px-6 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700">Create Story</button>
            </div>
          ) : (
            <div className="space-y-4">
              {myStories.map(story => (
                <div key={story.id} className="bg-white dark:bg-gray-800 rounded-xl p-5 border border-gray-200 dark:border-gray-700 flex items-center justify-between flex-wrap gap-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-gray-900 dark:text-white">{story.title}</h3>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 flex-wrap">
                      <span>{story.destination}</span><span>{story.format}</span>
                      <span className={`px-2 py-0.5 rounded-full ${story.status === 'published' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'}`}>{story.status}</span>
                      <span>👍 {story.likes_count}</span>
                      <span>👎 {story.dislikes_count ?? 0}</span>
                      <span>💬 {story.comments_count ?? 0}</span>
                      <span>{story.views_count} views</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    {story.status === 'draft' && (
                      <button onClick={() => publishStory(story.id)} className="px-3 py-1.5 bg-green-500 text-white rounded-lg text-xs hover:bg-green-600">Publish</button>
                    )}
                    <button onClick={() => viewStory(story.share_token)} className="px-3 py-1.5 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-xs hover:bg-gray-300">View</button>
                    <button onClick={() => shareStory(story)} className="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs hover:bg-blue-600">Share</button>
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
