import { useState, useRef, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Loading from '@/components/common/Loading';
import api from '@/services/api';

// ── Types ──

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface ExtractedParams {
  origin?: string;
  destination?: string;
  departure_date?: string;
  return_date?: string;
  passengers?: number;
  budget?: number | null;
  cuisine?: string;
}

interface TravelChatProps {
  onPlanReady: (result: any) => void;
  onParamsExtracted?: (params: ExtractedParams) => void;
  initialVoiceEnabled?: boolean;
}

// ── Component ──

const TravelChat = ({ onPlanReady, onParamsExtracted, initialVoiceEnabled = false }: TravelChatProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Hi! I'm your AI travel assistant. Tell me about your trip — where you'd like to go, when, your budget, and any preferences. I'll handle the rest!\n\nFor example: *\"I want to fly from New York to Paris next Friday for a week, budget $3000, love French cuisine\"*",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [planning, setPlanning] = useState(false);
  const [extractedParams, setExtractedParams] = useState<ExtractedParams>({});
  const [paramsComplete, setParamsComplete] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(initialVoiceEnabled);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Notify parent when params change
  useEffect(() => {
    onParamsExtracted?.(extractedParams);
  }, [extractedParams, onParamsExtracted]);

  // ── Send message to NLP backend ──
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = { role: 'user', content: text.trim(), timestamp: new Date() };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setLoading(true);

      try {
        const response = await api.post('/api/agents/chat', {
          message: text.trim(),
          conversation: messages
            .filter((m) => m.role !== 'system')
            .map((m) => ({ role: m.role, content: m.content })),
          extracted_params: extractedParams,
          confirmed: false,
        }, { timeout: 90000 });

        const data = response.data;

        if (data.success) {
          const assistantMsg: ChatMessage = {
            role: 'assistant',
            content: data.reply,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMsg]);
          setExtractedParams(data.extracted_params || {});
          setParamsComplete(data.params_complete || false);

          // Speak the reply if voice mode is on
          if (voiceEnabled) {
            speakText(data.reply);
          }
        } else {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `Sorry, I encountered an error: ${data.error || 'Unknown error'}. Please try again.`,
              timestamp: new Date(),
            },
          ]);
        }
      } catch (err: any) {
        const errorMsg = err?.response?.data?.error || err?.response?.data?.detail || err?.message || err?.code || 'Could not reach the server';
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Sorry, something went wrong: ${errorMsg}. Please try again.`,
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [messages, extractedParams, voiceEnabled]
  );

  // ── Confirm and trigger planning ──
  const handleConfirmPlan = async () => {
    setPlanning(true);
    setMessages((prev) => [
      ...prev,
      {
        role: 'system',
        content: 'Starting AI travel planning with your parameters...',
        timestamp: new Date(),
      },
    ]);

    try {
      const response = await api.post('/api/agents/chat', {
        message: '',
        conversation: [],
        extracted_params: extractedParams,
        confirmed: true,
      }, { timeout: 300000 });

      const data = response.data;

      if (data.success && data.planning_result) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Your trip has been planned! Scroll down to see the full results.',
            timestamp: new Date(),
          },
        ]);
        onPlanReady(data.planning_result);

        if (voiceEnabled) {
          speakText('Your trip has been planned! Scroll down to see the full results.');
        }
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Planning failed: ${data.error || 'Unknown error'}. Please try again.`,
            timestamp: new Date(),
          },
        ]);
      }
    } catch (err: any) {
      const errorMsg = err?.response?.data?.error || err?.response?.data?.detail || err?.message || err?.code || 'Could not reach the server';
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Planning failed: ${errorMsg}. Please try again.`,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setPlanning(false);
    }
  };

  // ── Voice Input (Web Speech API) ──
  const startListening = useCallback(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'system',
          content: 'Voice input is not supported in your browser. Please use Chrome or Edge.',
          timestamp: new Date(),
        },
      ]);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInput(transcript);

      // If final result, send automatically
      if (event.results[event.results.length - 1].isFinal) {
        setIsListening(false);
        if (transcript.trim()) {
          sendMessage(transcript.trim());
        }
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [sendMessage]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  // ── Voice Output (OpenAI TTS with browser fallback) ──
  const speakText = async (text: string) => {
    // Stop any current speech
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    // Strip markdown for speech
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/#{1,3}\s/g, '')
      .replace(/\[.*?\]\(.*?\)/g, '')
      .replace(/\n/g, '. ')
      .slice(0, 1000);

    setIsSpeaking(true);

    try {
      const response = await api.post('/api/agents/tts', { text: cleanText }, {
        responseType: 'blob',
      });

      if (response.status === 200) {
        const blob = response.data;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
          audioRef.current = null;
        };
        audio.onerror = () => {
          setIsSpeaking(false);
          URL.revokeObjectURL(url);
          audioRef.current = null;
        };

        await audio.play();
      } else {
        // Fallback to browser TTS
        fallbackSpeak(cleanText);
      }
    } catch {
      // Fallback to browser TTS
      fallbackSpeak(cleanText);
    }
  };

  const fallbackSpeak = (text: string) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeaking(false);
    }
  };

  const stopSpeaking = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  // ── Handle form submit ──
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      sendMessage(input);
    }
  };

  // ── Handle Enter key ──
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !loading) {
        sendMessage(input);
      }
    }
  };

  // ── Param display badge ──
  const paramBadge = (label: string, value: any) => {
    if (!value) return null;
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
        {label}: {String(value)}
      </span>
    );
  };

  return (
    <Card className="flex flex-col" style={{ maxHeight: '700px' }}>
      <CardHeader className="flex-shrink-0 pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">
            {voiceEnabled ? '🎙️ Voice & Chat Assistant' : '💬 Chat Assistant'}
          </CardTitle>
          <div className="flex items-center gap-2">
            {/* Voice toggle */}
            <button
              onClick={() => {
                setVoiceEnabled(!voiceEnabled);
                if (voiceEnabled) stopSpeaking();
              }}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                voiceEnabled
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                  : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
              }`}
              title={voiceEnabled ? 'Disable voice mode' : 'Enable voice mode'}
            >
              {voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off'}
            </button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col flex-1 min-h-0 pt-0">
        {/* Extracted params summary */}
        {Object.values(extractedParams).some((v) => v) && (
          <div className="flex flex-wrap gap-1.5 pb-3 border-b border-gray-200 dark:border-gray-700 mb-3">
            {paramBadge('From', extractedParams.origin)}
            {paramBadge('To', extractedParams.destination)}
            {paramBadge('Depart', extractedParams.departure_date)}
            {paramBadge('Return', extractedParams.return_date)}
            {paramBadge('Guests', extractedParams.passengers)}
            {extractedParams.budget && paramBadge('Budget', `$${extractedParams.budget}`)}
            {paramBadge('Cuisine', extractedParams.cuisine)}
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1" style={{ minHeight: '200px', maxHeight: '400px' }}>
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white rounded-br-md'
                    : msg.role === 'system'
                    ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200 border border-yellow-200 dark:border-yellow-800 rounded-bl-md'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-md'
                }`}
              >
                <div
                  dangerouslySetInnerHTML={{
                    __html: msg.content
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.*?)\*/g, '<em>$1</em>')
                      .replace(/\n/g, '<br/>'),
                  }}
                />
                {/* Speak button for assistant messages */}
                {msg.role === 'assistant' && voiceEnabled && (
                  <button
                    onClick={() => (isSpeaking ? stopSpeaking() : speakText(msg.content))}
                    className="mt-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    title={isSpeaking ? 'Stop speaking' : 'Read aloud'}
                  >
                    {isSpeaking ? '⏹ Stop' : '🔊 Listen'}
                  </button>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-md px-4 py-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Planning in progress */}
        {planning && (
          <div className="pb-3">
            <Loading size="sm" text="AI agents are planning your trip..." />
          </div>
        )}

        {/* Confirm button when params are complete */}
        {paramsComplete && !planning && (
          <div className="pb-3">
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
              <p className="text-sm text-green-800 dark:text-green-200 mb-2">
                I have all the details I need. Ready to plan your trip?
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={handleConfirmPlan}
                  size="sm"
                  disabled={planning}
                  className="bg-green-600 hover:bg-green-700"
                >
                  Plan My Trip!
                </Button>
                <Button
                  onClick={() => {
                    setParamsComplete(false);
                    sendMessage("I'd like to change something");
                  }}
                  size="sm"
                  variant="outline"
                >
                  Change Details
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Input area */}
        <form onSubmit={handleSubmit} className="flex gap-2 items-end flex-shrink-0">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isListening
                  ? 'Listening...'
                  : voiceEnabled
                  ? 'Type or click the mic to speak...'
                  : 'Type your travel request...'
              }
              className={`w-full px-4 py-2.5 pr-12 border rounded-xl resize-none text-sm
                bg-white dark:bg-gray-800 text-gray-900 dark:text-white
                focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                ${isListening
                  ? 'border-red-400 dark:border-red-500 animate-pulse'
                  : 'border-gray-300 dark:border-gray-600'
                }`}
              rows={1}
              disabled={loading || planning}
            />
            {/* Mic button inside input */}
            <button
              type="button"
              onClick={isListening ? stopListening : startListening}
              className={`absolute right-2 bottom-2 p-1.5 rounded-full transition-colors ${
                isListening
                  ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 animate-pulse'
                  : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title={isListening ? 'Stop listening' : 'Start voice input'}
              disabled={loading || planning}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
            </button>
          </div>
          <Button
            type="submit"
            size="sm"
            disabled={!input.trim() || loading || planning}
            className="rounded-xl px-4 py-2.5"
          >
            Send
          </Button>
        </form>

        {/* Voice status bar */}
        {(isListening || isSpeaking) && (
          <div className="mt-2 flex items-center gap-2 text-xs">
            {isListening && (
              <span className="flex items-center gap-1 text-red-600 dark:text-red-400">
                <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                Listening...
              </span>
            )}
            {isSpeaking && (
              <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                Speaking...
                <button
                  onClick={stopSpeaking}
                  className="ml-1 underline hover:no-underline"
                >
                  Stop
                </button>
              </span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TravelChat;
