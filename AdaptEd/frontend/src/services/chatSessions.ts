import api from './api';

export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ChatMessage {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: string;
  emotion?: 'happy' | 'thinking' | 'excited' | 'encouraging' | 'surprised';
  quickReplies?: Array<{ text: string }>;
}

export interface ChatSessionDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export async function listChatSessions(userId: string) {
  const { data } = await api.get<ChatSessionSummary[]>(`/assistant/chats/${userId}`);
  return data;
}

export async function createChatSession(userId: string, title?: string) {
  const { data } = await api.post<ChatSessionDetail>('/assistant/chats', {
    user_id: userId,
    title,
  });
  return data;
}

export async function getChatSession(userId: string, chatId: string) {
  const { data } = await api.get<ChatSessionDetail>(`/assistant/chats/${userId}/${chatId}`);
  return data;
}

export async function renameChatSession(userId: string, chatId: string, title: string) {
  const { data } = await api.put<ChatSessionDetail>(`/assistant/chats/${userId}/${chatId}`, { title });
  return data;
}

export async function deleteChatSession(userId: string, chatId: string) {
  const { data } = await api.delete<{ ok: boolean }>(`/assistant/chats/${userId}/${chatId}`);
  return data;
}

export async function saveChatSessionMessages(userId: string, chatId: string, messages: ChatMessage[]) {
  const { data } = await api.put<ChatSessionDetail>(`/assistant/chats/${userId}/${chatId}/messages`, { messages });
  return data;
}

