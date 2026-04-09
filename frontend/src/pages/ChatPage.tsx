import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { WS_BASE_URL } from '@/utils/constants';
import { getAuthToken } from '@/utils/helpers';
import {
  PaperAirplaneIcon,
  PlusIcon,
  ChatBubbleLeftRightIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

interface ConversationSummary {
  id: string;
  title: string;
  lastMessage: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Simple Markdown Renderer
// ---------------------------------------------------------------------------

function renderMarkdown(text: string): string {
  let html = text
    // Escape HTML entities
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 underline hover:text-blue-800 dark:hover:text-blue-300">$1</a>');

  // Process line-by-line for block elements
  const lines = html.split('\n');
  const result: string[] = [];
  let inList = false;
  let listType: 'ul' | 'ol' | null = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Headings
    if (/^### (.+)/.test(line)) {
      if (inList) { result.push(listType === 'ol' ? '</ol>' : '</ul>'); inList = false; listType = null; }
      result.push(`<h3 class="text-base font-semibold mt-3 mb-1">${line.replace(/^### /, '')}</h3>`);
      continue;
    }
    if (/^## (.+)/.test(line)) {
      if (inList) { result.push(listType === 'ol' ? '</ol>' : '</ul>'); inList = false; listType = null; }
      result.push(`<h2 class="text-lg font-semibold mt-3 mb-1">${line.replace(/^## /, '')}</h2>`);
      continue;
    }
    if (/^# (.+)/.test(line)) {
      if (inList) { result.push(listType === 'ol' ? '</ol>' : '</ul>'); inList = false; listType = null; }
      result.push(`<h1 class="text-xl font-bold mt-3 mb-1">${line.replace(/^# /, '')}</h1>`);
      continue;
    }

    // Unordered list
    if (/^[-*]\s+(.+)/.test(line)) {
      if (!inList || listType !== 'ul') {
        if (inList) result.push(listType === 'ol' ? '</ol>' : '</ul>');
        result.push('<ul class="list-disc list-inside space-y-0.5 ml-2">');
        inList = true;
        listType = 'ul';
      }
      result.push(`<li>${line.replace(/^[-*]\s+/, '')}</li>`);
      continue;
    }

    // Ordered list
    if (/^\d+\.\s+(.+)/.test(line)) {
      if (!inList || listType !== 'ol') {
        if (inList) result.push(listType === 'ol' ? '</ol>' : '</ul>');
        result.push('<ol class="list-decimal list-inside space-y-0.5 ml-2">');
        inList = true;
        listType = 'ol';
      }
      result.push(`<li>${line.replace(/^\d+\.\s+/, '')}</li>`);
      continue;
    }

    // End list if we hit a non-list line
    if (inList) {
      result.push(listType === 'ol' ? '</ol>' : '</ul>');
      inList = false;
      listType = null;
    }

    // Blank line -> paragraph break
    if (line.trim() === '') {
      result.push('<br/>');
    } else {
      result.push(`<p class="mb-1">${line}</p>`);
    }
  }

  if (inList) {
    result.push(listType === 'ol' ? '</ol>' : '</ul>');
  }

  return result.join('\n');
}

// ---------------------------------------------------------------------------
// Chat Bubble Components
// ---------------------------------------------------------------------------

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

const UserBubble = ({ message }: { message: ChatMessage }) => (
  <div className="flex justify-end mb-4 px-2">
    <div className="max-w-[75%] lg:max-w-[60%]">
      <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-md">
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </div>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 text-right">
        {formatTimestamp(message.timestamp)}
      </p>
    </div>
  </div>
);

const AssistantBubble = ({ message }: { message: ChatMessage }) => (
  <div className="flex justify-start mb-4 px-2">
    <div className="max-w-[80%] lg:max-w-[70%]">
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold shadow-md mt-1">
          AI
        </div>
        <div>
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-4 py-3 rounded-2xl rounded-bl-md shadow-md border border-gray-100 dark:border-gray-700">
            <div
              className="text-sm leading-relaxed text-gray-800 dark:text-gray-200 prose-sm"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
            />
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-violet-500 rounded-sm ml-0.5 animate-pulse" />
            )}
          </div>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 ml-1">
            {formatTimestamp(message.timestamp)}
          </p>
        </div>
      </div>
    </div>
  </div>
);

const TypingIndicator = () => (
  <div className="flex justify-start mb-4 px-2">
    <div className="flex items-start gap-2">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold shadow-md">
        AI
      </div>
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-4 py-3 rounded-2xl rounded-bl-md shadow-md border border-gray-100 dark:border-gray-700">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce [animation-delay:0ms]" />
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce [animation-delay:150ms]" />
          <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Quick Action Chips
// ---------------------------------------------------------------------------

const QUICK_ACTIONS = [
  { label: 'Plan a trip', icon: '🗺️' },
  { label: 'Find flights', icon: '✈️' },
  { label: 'Hotel deals', icon: '🏨' },
  { label: 'Restaurant recommendations', icon: '🍽️' },
];

// ---------------------------------------------------------------------------
// Main ChatPage Component
// ---------------------------------------------------------------------------

const ChatPage = () => {
  const [searchParams] = useSearchParams();
  const initialConversationId = searchParams.get('conversation') || undefined;

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [connected, setConnected] = useState(false);

  // Refs
  const socketRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamingMessageRef = useRef<Map<string, string>>(new Map());

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // ------------------------------------------------------------------
  // WebSocket connection
  // ------------------------------------------------------------------
  const connectWebSocket = useCallback((convId?: string) => {
    // Disconnect existing socket
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    const token = getAuthToken();
    if (!token) return;

    const wsPath = convId ? `/ws/chat/${convId}/` : '/ws/chat/';
    const base = WS_BASE_URL.replace(/^http/, 'ws');
    const url = `${base}${wsPath}?token=${encodeURIComponent(token)}`;

    const socket = new WebSocket(url);

    socket.onopen = () => {
      setConnected(true);
    };

    socket.onclose = () => {
      setConnected(false);
    };

    socket.onerror = () => {
      setConnected(false);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.type as string;

        switch (type) {
          case 'connection_established':
            setConversationId(data.conversation_id);
            break;

          case 'conversation_history':
            if (data.messages && Array.isArray(data.messages)) {
              setMessages(data.messages.map((m: ChatMessage) => ({ ...m, isStreaming: false })));
            }
            break;

          case 'conversation_list':
            if (data.conversations && Array.isArray(data.conversations)) {
              setConversations(data.conversations);
            }
            break;

          case 'agent_typing':
            setIsTyping(true);
            break;

          case 'agent_stream': {
            setIsTyping(false);
            const { token: tok, message_id } = data;

            streamingMessageRef.current.set(
              message_id,
              (streamingMessageRef.current.get(message_id) || '') + tok
            );

            const content = streamingMessageRef.current.get(message_id) || '';

            setMessages((prev) => {
              const idx = prev.findIndex((m) => m.id === message_id);
              if (idx === -1) {
                return [
                  ...prev,
                  {
                    id: message_id,
                    role: 'assistant',
                    content,
                    timestamp: new Date().toISOString(),
                    isStreaming: true,
                  },
                ];
              }
              const updated = [...prev];
              updated[idx] = { ...updated[idx], content, isStreaming: true };
              return updated;
            });
            break;
          }

          case 'agent_message_complete': {
            setIsTyping(false);
            const { message } = data;
            streamingMessageRef.current.delete(message.id);

            setMessages((prev) => {
              const idx = prev.findIndex((m: ChatMessage) => m.id === message.id);
              if (idx === -1) {
                return [...prev, { ...message, isStreaming: false }];
              }
              const updated = [...prev];
              updated[idx] = { ...message, isStreaming: false };
              return updated;
            });
            break;
          }

          case 'error':
            setIsTyping(false);
            setMessages((prev) => [
              ...prev,
              {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: `Sorry, something went wrong: ${data.message}`,
                timestamp: new Date().toISOString(),
                isStreaming: false,
              },
            ]);
            break;
        }
      } catch {
        // ignore non-JSON messages
      }
    };

    socketRef.current = socket;
  }, []);

  // Connect on mount
  useEffect(() => {
    connectWebSocket(conversationId);

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ------------------------------------------------------------------
  // Send message
  // ------------------------------------------------------------------
  const sendMessage = useCallback(
    (text?: string) => {
      const content = (text || input).trim();
      if (!content || socketRef.current?.readyState !== WebSocket.OPEN) return;

      // Add user message locally
      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Send via WebSocket
      socketRef.current.send(JSON.stringify({
        type: 'chat_message',
        message: content,
        conversation_id: conversationId,
      }));

      setInput('');
      setIsTyping(true);

      // Refocus input
      setTimeout(() => inputRef.current?.focus(), 50);
    },
    [input, conversationId]
  );

  // ------------------------------------------------------------------
  // New conversation
  // ------------------------------------------------------------------
  const startNewConversation = useCallback(() => {
    setMessages([]);
    setConversationId(undefined);
    streamingMessageRef.current.clear();
    setIsTyping(false);
    connectWebSocket();
    setSidebarOpen(false);
  }, [connectWebSocket]);

  // ------------------------------------------------------------------
  // Switch conversation
  // ------------------------------------------------------------------
  const switchConversation = useCallback(
    (convId: string) => {
      setMessages([]);
      setConversationId(convId);
      streamingMessageRef.current.clear();
      setIsTyping(false);
      connectWebSocket(convId);
      setSidebarOpen(false);
    },
    [connectWebSocket]
  );

  // ------------------------------------------------------------------
  // Handle textarea keydown (Enter to send, Shift+Enter for newline)
  // ------------------------------------------------------------------
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const target = e.target;
    target.style.height = 'auto';
    target.style.height = Math.min(target.scrollHeight, 150) + 'px';
  };

  // Is send disabled?
  const sendDisabled = !input.trim() || !connected;

  // Show welcome state when no messages
  const showWelcome = messages.length === 0 && !isTyping;

  // Memoize rendered messages
  const renderedMessages = useMemo(
    () =>
      messages.map((msg) =>
        msg.role === 'user' ? (
          <UserBubble key={msg.id} message={msg} />
        ) : (
          <AssistantBubble key={msg.id} message={msg} />
        )
      ),
    [messages]
  );

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* ---------- Hero Header ---------- */}
      <div className="bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 dark:from-violet-800 dark:via-purple-800 dark:to-indigo-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2">
                <ChatBubbleLeftRightIcon className="h-8 w-8" />
                AI Travel Assistant
              </h1>
              <p className="text-violet-200 dark:text-violet-300 mt-1 text-sm sm:text-base">
                Your personal AI-powered travel companion. Ask me anything about trips, flights, hotels, and more.
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* New Conversation Button */}
              <button
                onClick={startNewConversation}
                className="hidden sm:flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/15 hover:bg-white/25 backdrop-blur-sm text-white text-sm font-medium transition-all border border-white/20"
              >
                <PlusIcon className="h-4 w-4" />
                New Chat
              </button>
              {/* Mobile sidebar toggle */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-xl bg-white/15 hover:bg-white/25 backdrop-blur-sm text-white transition-all border border-white/20"
              >
                {sidebarOpen ? <XMarkIcon className="h-5 w-5" /> : <Bars3Icon className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ---------- Main Content Area ---------- */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* ---- Sidebar ---- */}
        {/* Backdrop for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={`
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            lg:translate-x-0 lg:static
            fixed top-0 left-0 z-40 lg:z-auto
            w-72 h-full
            bg-white/90 dark:bg-gray-900/95 backdrop-blur-md
            border-r border-gray-200 dark:border-gray-700
            transition-transform duration-300 ease-in-out
            flex flex-col
            lg:w-64 xl:w-72
          `}
        >
          {/* Sidebar header */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
              Conversations
            </h2>
            <button
              onClick={startNewConversation}
              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
              title="New conversation"
            >
              <PlusIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Conversation list */}
          <div className="flex-1 overflow-y-auto py-2">
            {conversations.length === 0 ? (
              <div className="px-4 py-8 text-center text-gray-400 dark:text-gray-500 text-sm">
                <ChatBubbleLeftRightIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                No conversations yet.
                <br />
                Start chatting!
              </div>
            ) : (
              conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => switchConversation(conv.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group ${
                    conversationId === conv.id
                      ? 'bg-violet-50 dark:bg-violet-900/20 border-r-2 border-violet-500'
                      : ''
                  }`}
                >
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">
                    {conv.title || 'Untitled conversation'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">
                    {conv.lastMessage}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    {formatTimestamp(conv.updatedAt)}
                  </p>
                </button>
              ))
            )}
          </div>

          {/* Mobile: close button at bottom */}
          <div className="lg:hidden p-3 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setSidebarOpen(false)}
              className="w-full py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            >
              Close sidebar
            </button>
          </div>
        </aside>

        {/* ---- Chat Area ---- */}
        <div className="flex-1 flex flex-col min-w-0 bg-gray-50 dark:bg-gray-900">
          {/* Connection status bar */}
          {!connected && (
            <div className="bg-amber-50 dark:bg-amber-900/30 border-b border-amber-200 dark:border-amber-700 px-4 py-2 text-center">
              <p className="text-xs text-amber-700 dark:text-amber-300">
                Connecting to AI assistant...
              </p>
            </div>
          )}

          {/* Messages area */}
          <div className="flex-1 overflow-y-auto px-2 sm:px-4 py-4">
            {showWelcome ? (
              /* Welcome state */
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg mb-6">
                  AI
                </div>
                <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">
                  Welcome to AI Travel Assistant
                </h2>
                <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
                  I can help you plan trips, find flights, discover hotels, recommend restaurants, and much more. What would you like to explore?
                </p>
                <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                  {QUICK_ACTIONS.map((action) => (
                    <button
                      key={action.label}
                      onClick={() => sendMessage(action.label)}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-violet-50 dark:hover:bg-violet-900/20 hover:border-violet-300 dark:hover:border-violet-600 hover:text-violet-700 dark:hover:text-violet-300 shadow-sm transition-all"
                    >
                      <span>{action.icon}</span>
                      {action.label}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              /* Messages list */
              <div className="max-w-4xl mx-auto">
                {renderedMessages}
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Quick actions strip (visible when there are messages) */}
          {messages.length > 0 && (
            <div className="px-4 pt-2 pb-0 max-w-4xl mx-auto w-full">
              <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => sendMessage(action.label)}
                    className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-violet-50 dark:hover:bg-violet-900/20 hover:border-violet-300 dark:hover:border-violet-600 hover:text-violet-700 dark:hover:text-violet-300 shadow-sm transition-all"
                  >
                    <span>{action.icon}</span>
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input area */}
          <div className="border-t border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm px-3 sm:px-4 py-3">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me about travel planning, flights, hotels..."
                    rows={1}
                    className="w-full resize-none rounded-2xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-4 py-3 pr-12 text-sm text-gray-800 dark:text-gray-200 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 dark:focus:ring-violet-400 focus:border-transparent transition-all shadow-sm"
                    style={{ maxHeight: '150px' }}
                  />
                </div>
                <button
                  onClick={() => sendMessage()}
                  disabled={sendDisabled}
                  className={`flex-shrink-0 p-3 rounded-xl shadow-md transition-all ${
                    sendDisabled
                      ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 text-white hover:shadow-lg active:scale-95'
                  }`}
                  title="Send message"
                >
                  <PaperAirplaneIcon className="h-5 w-5" />
                </button>
              </div>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
                AI Travel Assistant can make mistakes. Verify important travel details.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
