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
  { code: 'tr', name: 'Turkish', flag: '🇹🇷' },
];

export default function LanguageToolPage() {
  const [activeTab, setActiveTab] = useState<'translate' | 'phrases'>('translate');

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
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-3">
            Travel Language Toolkit
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-lg">
            Translate phrases and learn essential expressions for your destination
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="flex justify-center gap-4 mb-8">
          {(['translate', 'phrases'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2.5 rounded-full font-medium transition-all ${
                activeTab === tab
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-200 dark:shadow-purple-900/30'
                  : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
              }`}
            >
              {tab === 'translate' ? 'Translator' : 'Phrase Book'}
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
        </AnimatePresence>
      </div>
    </div>
  );
}
