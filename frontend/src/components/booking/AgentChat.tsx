import { useState, useRef, useEffect, useCallback } from 'react';
import {
  XMarkIcon,
  PaperAirplaneIcon,
  ChatBubbleLeftIcon,
  MicrophoneIcon,
  ArrowPathIcon,
  CheckIcon,
  StopIcon,
} from '@heroicons/react/24/outline';
import { useAgentChat } from '@/hooks/useAgentChat';
import useAuthStore from '@/store/authStore';
import { cn } from '@/utils/helpers';
import { LoadingSpinner } from '@/components/common/Loading';

const QUICK_PROMPTS = [
  { label: 'Plan a trip', prompt: 'I want to plan a new trip' },
  { label: 'My bookings', prompt: 'Show me my current bookings' },
  { label: 'Recommend a destination', prompt: 'Can you recommend a great travel destination?' },
  { label: 'Travel tips', prompt: 'Give me some travel tips for my next trip' },
];

const AgentChat = () => {
  const { isAuthenticated } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const {
    messages,
    sendMessage,
    confirmPlan,
    clearMessages,
    isLoading,
    extractedParams,
    paramsComplete,
  } = useAgentChat();

  // Only show chat for authenticated users
  if (!isAuthenticated) {
    return null;
  }

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');
        setInput(transcript);

        // If the result is final, auto-send
        if (event.results[event.results.length - 1].isFinal) {
          setIsListening(false);
        }
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleVoiceInput = useCallback(() => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setInput('');
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const msg = input.trim();
    setInput('');
    await sendMessage(msg);
  };

  const handleQuickPrompt = async (prompt: string) => {
    if (isLoading) return;
    await sendMessage(prompt);
  };

  const hasVoiceSupport = !!(
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  );

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 z-50 bg-primary-600 text-white p-3 sm:p-4 rounded-full shadow-lg hover:bg-primary-700 transition-all hover:scale-110 active:scale-95"
          aria-label="Open AI Travel Assistant"
        >
          <ChatBubbleLeftIcon className="h-5 w-5 sm:h-6 sm:w-6" />
        </button>
      )}

      {/* Chat window - full screen on mobile, floating on desktop */}
      {isOpen && (
        <div
          className={cn(
            'fixed z-50 bg-white dark:bg-gray-800 flex flex-col shadow-2xl',
            // Mobile: full screen
            'inset-0',
            // Desktop: floating panel
            'sm:inset-auto sm:bottom-4 sm:right-4 sm:w-[420px] sm:h-[640px] sm:max-h-[80vh] sm:rounded-xl'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700 bg-primary-600 sm:bg-white sm:dark:bg-gray-800 sm:rounded-t-xl">
            <div className="flex items-center space-x-2">
              <div className="h-2.5 w-2.5 bg-green-400 rounded-full animate-pulse" />
              <h3 className="font-semibold text-white sm:text-gray-900 sm:dark:text-white text-sm sm:text-base">
                AI Travel Assistant
              </h3>
            </div>
            <div className="flex items-center space-x-2">
              {messages.length > 0 && (
                <button
                  onClick={clearMessages}
                  className="text-white/80 sm:text-gray-400 hover:text-white sm:hover:text-gray-600 sm:dark:hover:text-gray-300 p-1"
                  title="Clear chat"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-white/80 sm:text-gray-400 hover:text-white sm:hover:text-gray-600 sm:dark:hover:text-gray-300 p-1"
                aria-label="Close chat"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="bg-primary-50 dark:bg-primary-900/20 rounded-full p-4 mb-4">
                  <ChatBubbleLeftIcon className="h-10 w-10 text-primary-500" />
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Hi! I'm your AI travel assistant.
                </h4>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-xs">
                  Ask me anything about travel - plan trips, get recommendations,
                  check your bookings, or ask about destinations!
                </p>

                {/* Quick action chips */}
                <div className="flex flex-wrap justify-center gap-2">
                  {QUICK_PROMPTS.map((qp) => (
                    <button
                      key={qp.label}
                      onClick={() => handleQuickPrompt(qp.prompt)}
                      className="px-3 py-1.5 text-xs sm:text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-primary-50 hover:text-primary-700 dark:hover:bg-primary-900/30 dark:hover:text-primary-300 transition-colors"
                    >
                      {qp.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      'flex',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    <div
                      className={cn(
                        'max-w-[85%] rounded-2xl px-3.5 py-2.5',
                        message.role === 'user'
                          ? 'bg-primary-600 text-white rounded-br-md'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-md'
                      )}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                      <p
                        className={cn(
                          'text-[10px] mt-1',
                          message.role === 'user'
                            ? 'text-white/60'
                            : 'text-gray-400 dark:text-gray-500'
                        )}
                      >
                        {new Date(message.timestamp).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                ))}

                {/* Confirm trip planning button */}
                {paramsComplete && !isLoading && (
                  <div className="flex justify-center py-2">
                    <button
                      onClick={confirmPlan}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors text-sm font-medium shadow-md"
                    >
                      <CheckIcon className="h-4 w-4" />
                      <span>Plan My Trip!</span>
                    </button>
                  </div>
                )}

                {/* Extracted params pill */}
                {Object.keys(extractedParams).some((k) => extractedParams[k]) && (
                  <div className="flex flex-wrap gap-1.5 px-1">
                    {extractedParams.origin && (
                      <span className="text-[10px] px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full">
                        From: {extractedParams.origin}
                      </span>
                    )}
                    {extractedParams.destination && (
                      <span className="text-[10px] px-2 py-0.5 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-full">
                        To: {extractedParams.destination}
                      </span>
                    )}
                    {extractedParams.departure_date && (
                      <span className="text-[10px] px-2 py-0.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-full">
                        {extractedParams.departure_date}
                      </span>
                    )}
                    {extractedParams.budget && (
                      <span className="text-[10px] px-2 py-0.5 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 rounded-full">
                        ${extractedParams.budget}
                      </span>
                    )}
                  </div>
                )}
              </>
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 dark:bg-gray-700 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <LoadingSpinner className="h-4 w-4 text-primary-500" />
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Thinking...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input area */}
          <form
            onSubmit={handleSubmit}
            className="p-3 sm:p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 sm:rounded-b-xl"
          >
            <div className="flex items-center space-x-2">
              {/* Voice input button */}
              {hasVoiceSupport && (
                <button
                  type="button"
                  onClick={toggleVoiceInput}
                  className={cn(
                    'flex-shrink-0 p-2 rounded-full transition-all',
                    isListening
                      ? 'bg-red-500 text-white animate-pulse'
                      : 'text-gray-400 hover:text-primary-600 hover:bg-gray-100 dark:hover:bg-gray-700'
                  )}
                  title={isListening ? 'Stop listening' : 'Voice input'}
                >
                  {isListening ? (
                    <StopIcon className="h-5 w-5" />
                  ) : (
                    <MicrophoneIcon className="h-5 w-5" />
                  )}
                </button>
              )}

              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  isListening ? 'Listening...' : 'Ask me anything about travel...'
                }
                className={cn(
                  'flex-1 px-3 py-2 text-sm border rounded-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent focus:bg-white dark:focus:bg-gray-600 transition-colors',
                  isListening
                    ? 'border-red-300 dark:border-red-600'
                    : 'border-gray-200 dark:border-gray-600'
                )}
                disabled={isLoading}
              />

              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="flex-shrink-0 p-2 bg-primary-600 text-white rounded-full hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors active:scale-95"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Voice listening indicator on mobile */}
            {isListening && (
              <div className="mt-2 flex items-center justify-center space-x-1 text-xs text-red-500">
                <span className="inline-block h-1.5 w-1.5 bg-red-500 rounded-full animate-pulse" />
                <span>Listening... Speak now</span>
              </div>
            )}
          </form>
        </div>
      )}
    </>
  );
};

export default AgentChat;
