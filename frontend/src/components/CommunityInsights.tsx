import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import api from '@/services/api';

interface MediaItem {
  id: number;
  user: string;
  title: string;
  description: string;
  media_type: string;
  file: string;
  upvotes: number;
  created_at: string;
}

interface Story {
  id: number;
  user: string;
  title: string;
  content: string;
  cover_image: string;
  rating: number | null;
  upvotes: number;
  created_at: string;
}

interface Tip {
  id: number;
  user: string;
  title: string;
  content: string;
  category: string;
  category_display: string;
  upvotes: number;
  created_at: string;
}

interface DestInfo {
  destination: string;
  country: string;
  summary: string;
  history: string;
  culture: string;
  customs_etiquette: string;
  currency: string;
  local_language: string;
  common_phrases: Record<string, string>;
  emergency_numbers: Record<string, string>;
}

interface CommunityData {
  destination: string;
  info: DestInfo | null;
  media: MediaItem[];
  stories: Story[];
  tips: Tip[];
  counts: { media: number; stories: number; tips: number };
}

const CATEGORY_ICONS: Record<string, string> = {
  money_saving: '\uD83D\uDCB0',
  safety: '\uD83D\uDEE1\uFE0F',
  food: '\uD83C\uDF7D\uFE0F',
  transport: '\uD83D\uDE8C',
  culture: '\uD83C\uDFAD',
  general: '\uD83D\uDCA1',
};

export default function CommunityInsights({ destination }: { destination: string }) {
  const [data, setData] = useState<CommunityData | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'info' | 'tips' | 'stories' | 'media'>('info');

  useEffect(() => {
    if (!destination) return;
    setLoading(true);
    api.get(`/api/community/destination-content/${encodeURIComponent(destination)}/`)
      .then((res) => setData(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [destination]);

  const upvote = async (type: 'media' | 'stories' | 'tips', id: number) => {
    try {
      await api.post(`/api/community/${type}/${id}/upvote/`);
      if (data) {
        const updated = { ...data };
        const list = updated[type] as Array<{ id: number; upvotes: number }>;
        const item = list.find((i) => i.id === id);
        if (item) item.upvotes += 1;
        setData({ ...updated });
      }
    } catch {
      // silent
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm p-8 text-center">
        <div className="animate-spin w-6 h-6 border-3 border-teal-600 border-t-transparent rounded-full mx-auto" />
        <p className="text-sm text-gray-500 mt-2">Loading community insights...</p>
      </div>
    );
  }

  if (!data) return null;

  const totalContent = data.counts.media + data.counts.stories + data.counts.tips;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-4">
        <h3 className="text-lg font-bold text-white">{destination} Community</h3>
        <p className="text-indigo-100 text-sm">
          {totalContent > 0
            ? `${totalContent} contribution${totalContent !== 1 ? 's' : ''} from travelers`
            : 'Be the first to contribute!'}
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {(['info', 'tips', 'stories', 'media'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2.5 text-sm font-medium transition-all border-b-2 ${
              tab === t
                ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'info' ? 'About' : t === 'tips' ? `Tips (${data.counts.tips})` : t === 'stories' ? `Stories (${data.counts.stories})` : `Media (${data.counts.media})`}
          </button>
        ))}
      </div>

      <div className="p-4 max-h-[500px] overflow-y-auto">
        {/* About / Destination Info */}
        {tab === 'info' && (
          <div className="space-y-4">
            {data.info ? (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400">{data.info.summary}</p>
                {data.info.culture && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Culture</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{data.info.culture}</p>
                  </div>
                )}
                {data.info.customs_etiquette && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">Customs & Etiquette</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{data.info.customs_etiquette}</p>
                  </div>
                )}
                {data.info.common_phrases && Object.keys(data.info.common_phrases).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Useful Phrases ({data.info.local_language})</h4>
                    <div className="grid grid-cols-2 gap-1.5">
                      {Object.entries(data.info.common_phrases).map(([key, val]) => (
                        <div key={key} className="px-2 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-700/50 text-xs">
                          <span className="text-gray-500">{key}:</span>{' '}
                          <span className="font-medium text-gray-900 dark:text-white">{val}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {data.info.currency && (
                  <p className="text-sm text-gray-500">
                    <span className="font-medium">Currency:</span> {data.info.currency}
                  </p>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500 text-center py-4">
                No destination info available yet.
              </p>
            )}
          </div>
        )}

        {/* Tips */}
        {tab === 'tips' && (
          <div className="space-y-3">
            {data.tips.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No tips yet. Share your knowledge!</p>
            ) : (
              data.tips.map((tip) => (
                <motion.div
                  key={tip.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-xl border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span>{CATEGORY_ICONS[tip.category] || '\uD83D\uDCA1'}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium">
                      {tip.category_display}
                    </span>
                  </div>
                  <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-1">{tip.title}</h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{tip.content}</p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>by {tip.user}</span>
                    <button
                      onClick={() => upvote('tips', tip.id)}
                      className="flex items-center gap-1 hover:text-indigo-600 transition-colors"
                    >
                      &#9650; {tip.upvotes}
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}

        {/* Stories */}
        {tab === 'stories' && (
          <div className="space-y-3">
            {data.stories.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No stories yet. Share your travel experience!</p>
            ) : (
              data.stories.map((story) => (
                <motion.div
                  key={story.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-3 rounded-xl border border-gray-200 dark:border-gray-700"
                >
                  <h4 className="font-semibold text-sm text-gray-900 dark:text-white mb-1">{story.title}</h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-3">{story.content}</p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <div className="flex items-center gap-2">
                      <span>by {story.user}</span>
                      {story.rating && (
                        <span className="text-yellow-500">{'&#9733;'.repeat(Math.round(story.rating))}</span>
                      )}
                    </div>
                    <button
                      onClick={() => upvote('stories', story.id)}
                      className="flex items-center gap-1 hover:text-indigo-600 transition-colors"
                    >
                      &#9650; {story.upvotes}
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        )}

        {/* Media */}
        {tab === 'media' && (
          <div>
            {data.media.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">No photos or media yet. Upload yours!</p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {data.media.map((item) => (
                  <div key={item.id} className="rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                    {item.media_type === 'photo' ? (
                      <img
                        src={item.file}
                        alt={item.title}
                        className="w-full h-32 object-cover"
                      />
                    ) : (
                      <div className="w-full h-32 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                        <span className="text-2xl">
                          {item.media_type === 'audio' ? '\uD83C\uDFB5' : item.media_type === 'video' ? '\uD83C\uDFA5' : '\uD83D\uDCC4'}
                        </span>
                      </div>
                    )}
                    <div className="p-2">
                      <p className="text-xs font-medium text-gray-900 dark:text-white truncate">{item.title}</p>
                      <div className="flex items-center justify-between text-xs text-gray-400 mt-1">
                        <span>{item.user}</span>
                        <button
                          onClick={() => upvote('media', item.id)}
                          className="hover:text-indigo-600"
                        >
                          &#9650; {item.upvotes}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
