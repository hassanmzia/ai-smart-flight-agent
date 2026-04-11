import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '@/services/api';

interface TranslationResult {
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  transliteration?: string;
  cultural_notes?: string;
}

interface PhrasePack {
  category: string;
  phrases: Array<{ english: string; translated: string; pronunciation: string }>;
}

const LANGUAGES = [
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'de', name: 'German', flag: '🇩🇪' },
  { code: 'it', name: 'Italian', flag: '🇮🇹' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
  { code: 'ko', name: 'Korean', flag: '🇰🇷' },
  { code: 'zh', name: 'Chinese', flag: '🇨🇳' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
  { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali', flag: '🇧🇩' },
  { code: 'tr', name: 'Turkish', flag: '🇹🇷' },
];

interface OfflinePack {
  language: string;
  code: string;
  phrases: Array<{ category: string; original: string; translated: string; pronunciation: string }>;
}

export default function LanguageToolPage() {
  const [activeTab, setActiveTab] = useState<'translate' | 'phrases' | 'voice' | 'offline'>('translate');

  // Translation state
  const [text, setText] = useState('');
  const [targetLang, setTargetLang] = useState('es');
  const [translating, setTranslating] = useState(false);
  const [result, setResult] = useState<TranslationResult | null>(null);

  // Phrase book state
  const [phraseLang, setPhraseLang] = useState('es');
  const [phrasePacks, setPhrasePacks] = useState<PhrasePack[]>([]);
  const [loadingPhrases, setLoadingPhrases] = useState(false);
  const [phrasesLoaded, setPhrasesLoaded] = useState('');
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // Voice translation state
  const [voiceText, setVoiceText] = useState('');
  const [voiceSourceLang, setVoiceSourceLang] = useState('en');
  const [voiceTargetLang, setVoiceTargetLang] = useState('es');
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceResult, setVoiceResult] = useState<{ translated_text: string; audio_url?: string } | null>(null);

  // Offline pack state
  const [offlineLang, setOfflineLang] = useState('es');
  const [offlinePack, setOfflinePack] = useState<OfflinePack | null>(null);
  const [offlineLoading, setOfflineLoading] = useState(false);

  const handleTranslate = async () => {
    if (!text.trim()) return;
    setTranslating(true);
    setResult(null);
    try {
      const res = await api.post('/api/agents/translate', {
        text: text.trim(),
        target_language: targetLang,
        context: 'travel',
      });
      setResult(res.data);
    } catch {
      setResult({
        original_text: text,
        translated_text: '(Translation unavailable — please try again)',
        source_language: 'en',
        target_language: targetLang,
      });
    } finally {
      setTranslating(false);
    }
  };

  const loadPhrases = async (lang: string) => {
    setPhraseLang(lang);
    if (phrasesLoaded === lang) return;
    setLoadingPhrases(true);
    try {
      const res = await api.get(`/api/agents/common-phrases?language=${lang}`);
      setPhrasePacks(res.data.phrases || []);
      setPhrasesLoaded(lang);
      setExpandedCategory(null);
    } catch {
      setPhrasePacks([]);
    } finally {
      setLoadingPhrases(false);
    }
  };

  const handleVoiceTranslate = async () => {
    if (!voiceText.trim()) return;
    setVoiceLoading(true);
    setVoiceResult(null);
    try {
      const res = await api.post('/api/agents/voice-translate', {
        text: voiceText.trim(),
        source_lang: voiceSourceLang,
        target_lang: voiceTargetLang,
      });
      setVoiceResult(res.data);
    } catch {
      setVoiceResult({ translated_text: '(Voice translation unavailable)' });
    } finally {
      setVoiceLoading(false);
    }
  };

  const handleDownloadOffline = async (lang: string) => {
    setOfflineLang(lang);
    setOfflineLoading(true);
    setOfflinePack(null);
    try {
      const res = await api.get(`/api/agents/offline-phrases?language=${lang}`);
      const pack = res.data?.pack;
      if (pack) {
        setOfflinePack(pack);
      }
    } catch {
      setOfflinePack(null);
    } finally {
      setOfflineLoading(false);
    }
  };

  const saveOfflinePack = () => {
    if (!offlinePack) return;
    const blob = new Blob([JSON.stringify(offlinePack, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `phrases-${offlinePack.code}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const langName = (code: string) =>
    LANGUAGES.find((l) => l.code === code)?.name || code;
  const langFlag = (code: string) =>
    LANGUAGES.find((l) => l.code === code)?.flag || '';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-10 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-3">
            Travel Language Toolkit
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Translate phrases and learn essential expressions for your destination
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex justify-center gap-2 sm:gap-4 mb-8 flex-wrap">
          {([
            { key: 'translate' as const, label: 'Translator' },
            { key: 'phrases' as const, label: 'Phrase Book' },
            { key: 'voice' as const, label: 'Voice Translate' },
            { key: 'offline' as const, label: 'Offline Packs' },
          ]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-5 py-2.5 rounded-full font-medium transition-all text-sm ${
                activeTab === tab.key
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-200 dark:shadow-purple-900/30'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {/* ──── Translator Tab ──── */}
          {activeTab === 'translate' && (
            <motion.div
              key="translate"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                {/* Language selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Translate to
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {LANGUAGES.map((l) => (
                      <button
                        key={l.code}
                        onClick={() => setTargetLang(l.code)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                          targetLang === l.code
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {l.flag} {l.name}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Text input */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    English text
                  </label>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Type a phrase to translate..."
                    rows={3}
                    className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>

                <button
                  onClick={handleTranslate}
                  disabled={!text.trim() || translating}
                  className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold disabled:opacity-50 transition-colors"
                >
                  {translating ? 'Translating...' : 'Translate'}
                </button>

                {/* Result */}
                {result && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 space-y-4"
                  >
                    <div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                        {langFlag(result.target_language)} {langName(result.target_language)}
                      </p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                        {result.translated_text}
                      </p>
                    </div>
                    {result.transliteration && (
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                          Pronunciation
                        </p>
                        <p className="text-lg text-gray-700 dark:text-gray-300 italic">
                          {result.transliteration}
                        </p>
                      </div>
                    )}
                    {result.cultural_notes && (
                      <div className="border-t border-purple-200 dark:border-purple-700 pt-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                          Cultural Note
                        </p>
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                          {result.cultural_notes}
                        </p>
                      </div>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Phrase Book Tab ──── */}
          {activeTab === 'phrases' && (
            <motion.div
              key="phrases"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                {/* Language selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Choose language
                  </label>
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                    {LANGUAGES.map((l) => (
                      <button
                        key={l.code}
                        onClick={() => loadPhrases(l.code)}
                        className={`flex flex-col items-center py-3 rounded-xl text-sm font-medium transition-all ${
                          phraseLang === l.code
                            ? 'bg-purple-600 text-white shadow-lg'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        <span className="text-xl mb-1">{l.flag}</span>
                        <span>{l.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {loadingPhrases && (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-4 border-purple-400 border-t-transparent rounded-full mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400">Loading phrases...</p>
                  </div>
                )}

                {!loadingPhrases && phrasePacks.length === 0 && phrasesLoaded === '' && (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <p className="text-4xl mb-3">&#128218;</p>
                    <p>Select a language above to load travel phrases</p>
                  </div>
                )}

                {/* Phrase categories */}
                {!loadingPhrases && phrasePacks.length > 0 && (
                  <div className="space-y-3">
                    {phrasePacks.map((pack) => (
                      <div
                        key={pack.category}
                        className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden"
                      >
                        <button
                          onClick={() =>
                            setExpandedCategory(
                              expandedCategory === pack.category ? null : pack.category
                            )
                          }
                          className="w-full flex items-center justify-between px-5 py-4 bg-gray-50 dark:bg-gray-750 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        >
                          <span className="font-semibold text-gray-900 dark:text-white capitalize">
                            {pack.category.replace(/_/g, ' ')}
                          </span>
                          <span
                            className={`transform transition-transform text-gray-400 ${
                              expandedCategory === pack.category ? 'rotate-180' : ''
                            }`}
                          >
                            &#9660;
                          </span>
                        </button>

                        <AnimatePresence>
                          {expandedCategory === pack.category && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="overflow-hidden"
                            >
                              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                                {pack.phrases.map((phrase, idx) => (
                                  <div
                                    key={idx}
                                    className="px-5 py-3 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4"
                                  >
                                    <span className="text-sm text-gray-500 dark:text-gray-400 sm:w-1/3">
                                      {phrase.english}
                                    </span>
                                    <span className="text-base font-medium text-gray-900 dark:text-white sm:w-1/3">
                                      {phrase.translated}
                                    </span>
                                    <span className="text-sm italic text-purple-600 dark:text-purple-400 sm:w-1/3">
                                      {phrase.pronunciation}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}
          {/* ──── Voice Translate Tab ──── */}
          {activeTab === 'voice' && (
            <motion.div
              key="voice"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Voice-to-Voice Translation
                </h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Type or paste text, get a translated result with optional audio playback.
                </p>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From</label>
                    <select
                      value={voiceSourceLang}
                      onChange={(e) => setVoiceSourceLang(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white"
                    >
                      <option value="en">English</option>
                      {LANGUAGES.map((l) => (
                        <option key={l.code} value={l.code}>{l.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To</label>
                    <select
                      value={voiceTargetLang}
                      onChange={(e) => setVoiceTargetLang(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-3 py-2 text-gray-900 dark:text-white"
                    >
                      {LANGUAGES.map((l) => (
                        <option key={l.code} value={l.code}>{l.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <textarea
                  value={voiceText}
                  onChange={(e) => setVoiceText(e.target.value)}
                  placeholder="Enter text to translate with voice..."
                  rows={3}
                  className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />

                <button
                  onClick={handleVoiceTranslate}
                  disabled={!voiceText.trim() || voiceLoading}
                  className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold disabled:opacity-50 transition-colors"
                >
                  {voiceLoading ? 'Translating...' : 'Translate with Voice'}
                </button>

                {voiceResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 space-y-4"
                  >
                    <p className="text-xl font-semibold text-gray-900 dark:text-white">
                      {voiceResult.translated_text}
                    </p>
                    {voiceResult.audio_url && (
                      <audio controls className="w-full mt-2">
                        <source src={voiceResult.audio_url} type="audio/mpeg" />
                        Your browser does not support audio playback.
                      </audio>
                    )}
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}

          {/* ──── Offline Packs Tab ──── */}
          {activeTab === 'offline' && (
            <motion.div
              key="offline"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6 md:p-8 space-y-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Offline Phrase Packs
                </h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm">
                  Download essential travel phrases for offline use. No internet needed once downloaded.
                </p>

                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {LANGUAGES.filter((l) => ['es', 'fr', 'ar', 'ja', 'hi', 'bn', 'tr'].includes(l.code)).map((l) => (
                    <button
                      key={l.code}
                      onClick={() => handleDownloadOffline(l.code)}
                      className={`flex flex-col items-center py-4 rounded-xl text-sm font-medium transition-all border-2 ${
                        offlineLang === l.code && offlinePack
                          ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-600'
                      }`}
                    >
                      <span className="text-2xl mb-1">{l.flag}</span>
                      <span className="text-gray-900 dark:text-white">{l.name}</span>
                    </button>
                  ))}
                </div>

                {offlineLoading && (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-4 border-purple-400 border-t-transparent rounded-full mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400">Preparing phrase pack...</p>
                  </div>
                )}

                {offlinePack && !offlineLoading && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    <div className="flex items-center justify-between">
                      <p className="text-gray-700 dark:text-gray-300">
                        <span className="font-semibold">{offlinePack.language}</span> — {offlinePack.phrases.length} phrases ready
                      </p>
                      <button
                        onClick={saveOfflinePack}
                        className="px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
                      >
                        Download JSON
                      </button>
                    </div>
                    <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-80 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700">
                      {offlinePack.phrases.map((p, i) => (
                        <div key={i} className="px-4 py-2 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 text-sm">
                          <span className="text-xs text-purple-600 dark:text-purple-400 uppercase w-20 shrink-0">{p.category}</span>
                          <span className="text-gray-500 dark:text-gray-400 sm:w-1/3">{p.original}</span>
                          <span className="font-medium text-gray-900 dark:text-white sm:w-1/3">{p.translated}</span>
                          <span className="italic text-gray-400 dark:text-gray-500 sm:w-1/4">{p.pronunciation}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
