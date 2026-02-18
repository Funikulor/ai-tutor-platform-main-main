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
  const { data } = await api.post<{ test: TestDetail }>('/tests/manual', payload);
  return data.test;
}

export async function generateTest(payload: GeneratedTestRequest) {
  const { data } = await api.post<{ test?: TestDetail } & Partial<TestDetail>>('/tests/generate', payload);

  if (data?.test) return data.test;
  if (data && (data.id !== undefined || data.title !== undefined || data.questions !== undefined)) {
    return data as TestDetail;
  }
  throw new Error('Неверный формат ответа от сервера');
}

export async function listTests(params?: { topic?: string; creator_id?: string }) {
  const { data } = await api.get<TestSummary[]>('/tests', { params });
  return data;
}

export async function getTest(id: number) {
  const { data } = await api.get<TestDetail>(`/tests/${id}`);
  return data;
}

export interface ManualTestUpdate {
  title?: string;
  topic?: string;
  difficulty?: string;
  questions?: ManualQuestion[];
}

export async function updateTest(id: number, payload: ManualTestUpdate) {
  const { data } = await api.put<{ test: TestDetail }>(`/tests/${id}`, payload);
  return data.test;
}

export async function deleteTest(id: number) {
  const { data } = await api.delete<{ ok: boolean }>(`/tests/${id}`);
  return data;
}

export async function assignTestAsHomework(testId: number, studentIds: string[], dueDate?: string) {
  const { data } = await api.post<{ success: boolean; homeworks: any[] }>('/tests/assign', {
    test_id: testId,
    student_ids: studentIds,
    due_date: dueDate,
  });
  return data;
}

