import api from './api';

export interface ManualQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation?: string;
}

export interface ManualTestCreate {
  title: string;
  topic?: string;
  difficulty?: string;
  creator_id?: string;
  questions: ManualQuestion[];
}

export interface GeneratedTestRequest {
  topic: string;
  difficulty?: string;
  question_count?: number;
  creator_id?: string;
  user_id?: string;
  subject?: string;
  grade?: string;
  include_explanations?: boolean;
}

export interface TestSummary {
  id: number;
  title: string;
  topic?: string;
  difficulty?: string;
  source?: string;
  creator_id?: string;
  created_at?: string;
}

export interface TestQuestion {
  id: number;
  question: string;
  options: string[];
  correct_index: number;
  question_type?: 'single' | 'multiple' | 'text' | 'numeric';
  explanation?: string;
}

export interface TestDetail extends TestSummary {
  questions: TestQuestion[];
}

export async function createManualTest(payload: ManualTestCreate) {
  const resp = await api.post<{ test: TestDetail }>('/tests/manual', payload);
  return resp.data.test;
}

export async function generateTest(payload: GeneratedTestRequest) {
  try {
    const resp = await api.post<{ test: TestDetail }>('/tests/generate', payload);
    // бэкенд возвращает { test: {...} }, но на всякий случай поддержим прямой объект
    const data = resp.data as any;
    
    // Логируем для отладки
    console.log('[tests] generate response data:', data);
    console.log('[tests] generate response data type:', typeof data);
    console.log('[tests] generate response data.test:', data?.test);
    console.log('[tests] generate response data.id:', data?.id);
    
    if (data && data.test) {
      return data.test as TestDetail;
    }
    if (data && data.id) {
      // Если вернулся прямой объект теста
      return data as TestDetail;
    }
    
    // Дополнительная проверка: возможно ответ пришел в другом формате
    if (data && typeof data === 'object') {
      // Проверяем, может быть это уже сам тест
      if (data.title !== undefined || data.questions !== undefined) {
        console.log('[tests] treating data as direct test object');
        return data as TestDetail;
      }
    }
    
    console.error('[tests] Unexpected response format:', JSON.stringify(data, null, 2));
    throw new Error('Неверный формат ответа от сервера');
  } catch (error: any) {
    // Пробрасываем ошибку дальше с правильной информацией
    if (error.response) {
      const detail = error.response.data?.detail || error.response.data?.message || error.response.statusText;
      const err = new Error(detail || 'Ошибка генерации теста');
      (err as any).response = error.response;
      throw err;
    }
    // Если это наша ошибка о формате, пробрасываем как есть
    if (error.message === 'Неверный формат ответа от сервера') {
      throw error;
    }
    throw error;
  }
}

export async function listTests(params?: { topic?: string; creator_id?: string }) {
  const resp = await api.get<TestSummary[]>('/tests', { params });
  return resp.data;
}

export async function getTest(id: number) {
  const resp = await api.get<TestDetail>(`/tests/${id}`);
  return resp.data;
}

export async function deleteTest(id: number) {
  const resp = await api.delete<{ ok: boolean }>(`/tests/${id}`);
  return resp.data;
}


