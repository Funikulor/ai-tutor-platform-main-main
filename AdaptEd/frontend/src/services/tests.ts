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
  const resp = await api.post<{ test: TestDetail }>('/tests/generate', payload);
  // бэкенд возвращает { test: {...} }, но на всякий случай поддержим прямой объект
  const data = resp.data as any;
  return (data && (data.test || data)) as TestDetail;
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


