import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { AICharacter } from './AICharacter';
import { Send, Sparkles, Minimize2, Plus, Pencil, Trash2 } from 'lucide-react';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import {
  ChatMessage as PersistedChatMessage,
  ChatSessionSummary,
  createChatSession,
  deleteChatSession,
  getChatSession,
  listChatSessions,
  renameChatSession,
  saveChatSessionMessages,
} from '../services/chatSessions';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  emotion?: 'happy' | 'thinking' | 'excited' | 'encouraging' | 'surprised';
}

/** Приводит LaTeX в формате \( \) и \[ \] к виду $ $ и $$ $$ для remark-math */
function normalizeLatexForMarkdown(text: string): string {
  if (!text) return text;
  return text
    .replace(/\\\[([\s\S]*?)\\\]/g, '$$$1$$')
    .replace(/\\\(([\s\S]*?)\\\)/g, '$$1$$');
}

interface AIChatPanelProps {
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  fullscreen?: boolean;
}

export function AIChatPanel({ isMinimized = false, onToggleMinimize, fullscreen = false }: AIChatPanelProps) {
  const userId = localStorage.getItem('user_id') || '';

  const getInitialMessage = (): Message => ({
    id: 1,
    text: 'Привет! Я твой AI-помощник 🌟 Готов помочь тебе с учебой! О чем хочешь поговорить?',
    sender: 'ai',
    timestamp: new Date(),
    emotion: 'happy',
  });

  // Fallback only when user_id is missing.
  const loadMessagesFromStorage = (): Message[] => {
    try {
      const saved = localStorage.getItem('ai_chat_messages');
      if (saved) {
        const parsed = JSON.parse(saved);
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      }
    } catch (e) {
      console.error('Error loading messages from storage:', e);
    }
    return [getInitialMessage()];
  };

  const [messages, setMessages] = useState<Message[]>(loadMessagesFromStorage);
  const [chatSessions, setChatSessions] = useState<ChatSessionSummary[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [loadingChats, setLoadingChats] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<'happy' | 'thinking' | 'excited' | 'encouraging' | 'surprised'>('happy');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const toPersisted = (nextMessages: Message[]): PersistedChatMessage[] =>
    nextMessages.map((m) => ({
      id: m.id,
      text: m.text,
      sender: m.sender,
      timestamp: m.timestamp.toISOString(),
      emotion: m.emotion,
    }));

  const fromPersisted = (saved: PersistedChatMessage[]): Message[] =>
    saved.map((m) => ({
      ...m,
      timestamp: new Date(m.timestamp),
    }));

  const persistCurrentChat = async (nextMessages: Message[]) => {
    if (!userId || !activeChatId) return;
    try {
      await saveChatSessionMessages(userId, activeChatId, toPersisted(nextMessages));
      const sessions = await listChatSessions(userId);
      setChatSessions(sessions);
    } catch (e) {
      console.error('Error saving chat session messages:', e);
    }
  };

  const openChat = async (chatId: string) => {
    if (!userId) return;
    try {
      const chat = await getChatSession(userId, chatId);
      const nextMessages = chat.messages?.length ? fromPersisted(chat.messages) : [getInitialMessage()];
      setActiveChatId(chatId);
      setMessages(nextMessages);
    } catch (e) {
      console.error('Error opening chat:', e);
    }
  };

  const handleCreateChat = async () => {
    if (!userId) {
      setMessages([getInitialMessage()]);
      return;
    }
    try {
      const created = await createChatSession(userId, 'Новый чат');
      const sessions = await listChatSessions(userId);
      setChatSessions(sessions);
      setActiveChatId(created.id);
      setMessages([getInitialMessage()]);
      await persistCurrentChat([getInitialMessage()]);
    } catch (e) {
      console.error('Error creating chat:', e);
    }
  };

  const handleRenameChat = async () => {
    if (!userId || !activeChatId) return;
    const current = chatSessions.find((c) => c.id === activeChatId);
    const nextTitle = prompt('Новое название чата', current?.title || 'Новый чат');
    if (!nextTitle || !nextTitle.trim()) return;
    try {
      await renameChatSession(userId, activeChatId, nextTitle.trim());
      setChatSessions(await listChatSessions(userId));
    } catch (e) {
      console.error('Error renaming chat:', e);
    }
  };

  const handleDeleteChat = async () => {
    if (!userId || !activeChatId) return;
    if (!confirm('Удалить этот чат?')) return;
    try {
      await deleteChatSession(userId, activeChatId);
      const sessions = await listChatSessions(userId);
      setChatSessions(sessions);
      if (sessions.length > 0) {
        await openChat(sessions[0].id);
      } else {
        await handleCreateChat();
      }
    } catch (e) {
      console.error('Error deleting chat:', e);
    }
  };

  useEffect(() => {
    const init = async () => {
      if (!userId) return;
      setLoadingChats(true);
      try {
        let sessions = await listChatSessions(userId);
        if (sessions.length === 0) {
          const created = await createChatSession(userId, 'Новый чат');
          sessions = await listChatSessions(userId);
          setActiveChatId(created.id);
          setMessages([getInitialMessage()]);
          await saveChatSessionMessages(userId, created.id, toPersisted([getInitialMessage()]));
        } else {
          await openChat(sessions[0].id);
        }
        setChatSessions(sessions);
      } catch (e) {
        console.error('Error initializing chat sessions:', e);
      } finally {
        setLoadingChats(false);
      }
    };
    init();
  }, [userId]);

  // Сохраняем активный чат в localStorage для совместимости со старыми метриками.
  useEffect(() => {
    try {
      localStorage.setItem('ai_chat_messages', JSON.stringify(messages));
      window.dispatchEvent(new Event('ai-chat-updated'));
    } catch (e) {
      console.error('Error saving messages to storage:', e);
    }
  }, [messages]);

  const starterQuestions = [
    { text: 'Расскажи про дроби', icon: '🔢' },
    { text: 'Помоги с задачей', icon: '📝' },
    { text: 'Почему небо голубое?', icon: '🌈' },
    { text: 'Как учить английский?', icon: '🌍' }
  ];

  const scrollToBottom = () => {
    // Прокручиваем только контейнер сообщений, а не всю страницу
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const determineEmotion = (text: string): typeof currentEmotion => {
    const lowerText = text.toLowerCase();
    if (lowerText.includes('🎉') || lowerText.includes('отлично') || lowerText.includes('супер')) {
      return 'excited';
    } else if (lowerText.includes('💪') || lowerText.includes('помогу') || lowerText.includes('поддерж')) {
      return 'encouraging';
    } else if (lowerText.includes('🤔') || lowerText.includes('думаю') || lowerText.includes('размышляю')) {
      return 'thinking';
    } else if (lowerText.includes('😊') || lowerText.includes('рад') || lowerText.includes('привет')) {
      return 'happy';
    }
    return 'happy';
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return;

    const trimmed = text.trim();
    // Сразу очищаем поле ввода, чтобы текст не оставался до отправки
    setInputValue('');

    // Add user message
    const userMessage: Message = {
      id: messages.length + 1,
      text: trimmed,
      sender: 'user',
      timestamp: new Date()
    };
    const nextWithUser = [...messages, userMessage];
    setMessages(nextWithUser);

    // Show typing indicator сразу после добавления сообщения
    setIsTyping(true);
    setCurrentEmotion('thinking');

    // Сохранение чата в фоне, не блокируем UI
    persistCurrentChat(nextWithUser).catch((e) => console.error('Error saving chat:', e));

    try {
      // Формируем историю сообщений для API
      const userName = localStorage.getItem('full_name') || undefined;
      const messageHistory = nextWithUser.map(msg => ({
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.text
      }));

      // Отправляем запрос на backend
      const response = await api.post('/assistant/chat', {
        messages: messageHistory,
        mode: 'general',
        user_id: localStorage.getItem('user_id') || null,
        user_name: userName,
      }, {
        timeout: 120000, // 120 секунд для OpenAI
      });

      const aiResponseText = response.data.message || 'Извините, не удалось получить ответ.';
      const emotion = determineEmotion(aiResponseText);

      const aiMessage: Message = {
        id: messages.length + 2,
        text: aiResponseText,
        sender: 'ai',
        timestamp: new Date(),
        emotion: emotion
      };

      const nextWithAi = [...nextWithUser, aiMessage];
      setMessages(nextWithAi);
      setCurrentEmotion(emotion);
      // Убираем индикатор загрузки сразу после ответа; сохранение — в фоне
      setIsTyping(false);
      persistCurrentChat(nextWithAi).catch((e) => console.error('Error saving chat:', e));
    } catch (error: any) {
      console.error('Chat error:', error);
      const errorMessage: Message = {
        id: messages.length + 2,
        text: error.response?.data?.detail || 'Произошла ошибка при отправке сообщения. Убедитесь, что backend запущен и API ключ задан (локально: .env; Railway: Variables).',
        sender: 'ai',
        timestamp: new Date(),
        emotion: 'thinking'
      };
      const nextWithError = [...nextWithUser, errorMessage];
      setMessages(nextWithError);
      setCurrentEmotion('thinking');
      setIsTyping(false);
      persistCurrentChat(nextWithError).catch((e) => console.error('Error saving chat:', e));
    }
  };

  // Слушаем события для отправки сообщений извне (например, из популярных тем)
  useEffect(() => {
    const handleChatSendMessage = (event: CustomEvent<{ message: string }>) => {
      if (event.detail?.message) {
        handleSendMessage(event.detail.message);
      }
    };

    window.addEventListener('chat-send-message', handleChatSendMessage as EventListener);
    return () => {
      window.removeEventListener('chat-send-message', handleChatSendMessage as EventListener);
    };
  }, []); // Пустой массив, handleSendMessage использует актуальное состояние через замыкание

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  if (isMinimized) {
    return (
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full shadow-lg flex items-center justify-center hover:scale-110 transition-transform z-50"
        onClick={onToggleMinimize}
      >
        <AICharacter size="small" emotion="happy" />
      </motion.button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`${fullscreen
          ? 'w-full h-full'
          : 'fixed bottom-6 right-6 w-96 h-[600px] shadow-2xl'
        } bg-white rounded-2xl flex flex-col overflow-hidden border-2 border-purple-200 z-40`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-500 to-blue-500 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <AICharacter size="small" emotion={currentEmotion} isSpeaking={isTyping} />
          <div className="text-white">
            <h3 className="text-white">AI Помощник</h3>
            <p className="text-xs text-purple-100">
              {loadingChats
                ? 'Загрузка чатов...'
                : chatSessions.find((c) => c.id === activeChatId)?.title || 'Всегда готов помочь!'}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCreateChat}
            className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center text-white"
            title="Новый чат"
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={handleRenameChat}
            disabled={!activeChatId}
            className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center text-white disabled:opacity-50"
            title="Переименовать чат"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={handleDeleteChat}
            disabled={!activeChatId}
            className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center text-white disabled:opacity-50"
            title="Удалить чат"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          {!fullscreen && (
            <button
              onClick={onToggleMinimize}
              className="w-8 h-8 rounded-lg bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center text-white"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {chatSessions.length > 0 && (
        <div className="px-4 py-2 bg-purple-50 border-b border-purple-100">
          <select
            value={activeChatId || ''}
            onChange={(e) => openChat(e.target.value)}
            className="w-full px-3 py-2 border border-purple-200 rounded-lg bg-white text-sm"
          >
            {chatSessions.map((session) => (
              <option key={session.id} value={session.id}>
                {session.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Messages Area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-purple-50/30 to-blue-50/30 overflow-x-hidden"
      >
        {messages.length === 1 && (
          <div className="mb-4">
            <p className="text-center text-gray-600 text-sm mb-3">Начни с вопроса или выбери тему:</p>
            <div className="grid grid-cols-2 gap-2">
              {starterQuestions.map((question, index) => (
                <motion.button
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => handleSendMessage(question.text)}
                  className="p-3 bg-white rounded-xl border-2 border-purple-200 hover:border-purple-400 hover:shadow-md transition-all text-left"
                >
                  <span className="text-2xl mb-1 block">{question.icon}</span>
                  <span className="text-xs text-gray-700">{question.text}</span>
                </motion.button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((message, index) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} items-end gap-2`}
            >
              {message.sender === 'ai' && (
                <div className="flex-shrink-0">
                  <AICharacter size="small" emotion={message.emotion || 'happy'} />
                </div>
              )}

              <div
                className={`max-w-[75%] min-w-0 p-3 rounded-2xl ${message.sender === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white rounded-br-sm'
                    : 'bg-white border-2 border-purple-200 text-gray-800 rounded-bl-sm shadow-sm'
                  }`}
              >
                <div className="prose prose-sm max-w-none break-words overflow-wrap-anywhere">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      p: ({node, ...props}) => <p className="break-words overflow-wrap-anywhere" {...props} />,
                      code: ({node, ...props}) => <code className="break-words overflow-wrap-anywhere whitespace-pre-wrap" {...props} />,
                      pre: ({node, ...props}) => <pre className="break-words overflow-wrap-anywhere whitespace-pre-wrap max-w-full overflow-x-auto" {...props} />
                    }}
                  >
                    {normalizeLatexForMarkdown(message.text)}
                  </ReactMarkdown>
                </div>
                <p className={`text-xs mt-1 ${message.sender === 'user' ? 'text-blue-100' : 'text-gray-400'
                  }`}>
                  {message.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>

              {message.sender === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white flex-shrink-0">
                  👤
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-end gap-2"
          >
            <div className="flex-shrink-0">
              <AICharacter size="small" emotion="thinking" isSpeaking={true} />
            </div>
            <div className="bg-white border-2 border-purple-200 rounded-2xl rounded-bl-sm p-3 shadow-sm">
              <div className="flex gap-1">
                <motion.div
                  className="w-2 h-2 bg-purple-400 rounded-full"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                />
                <motion.div
                  className="w-2 h-2 bg-purple-400 rounded-full"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                />
                <motion.div
                  className="w-2 h-2 bg-purple-400 rounded-full"
                  animate={{ y: [0, -8, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                />
              </div>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t-2 border-purple-100">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Напиши свой вопрос..."
            className="flex-1 px-4 py-3 bg-purple-50 border-2 border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent text-gray-800 placeholder-gray-500"
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center text-white hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 active:scale-95"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        <p className="text-xs text-gray-500 text-center mt-2 flex items-center justify-center gap-1">
          <Sparkles className="w-3 h-3 text-purple-400" />
          Работает на AI технологиях
        </p>
      </div>
    </motion.div>
  );
}
