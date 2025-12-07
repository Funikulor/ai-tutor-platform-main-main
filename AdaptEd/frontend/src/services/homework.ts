import api from './api';

export interface Homework {
  id: number;
  title: string;
  description?: string;
  subject?: string;
  due_date?: string;
  status: string;
  assigned_to: string;
  created_by?: string;
  created_at: string;
}

export interface HomeworkSubmissionPayload {
  answer_text?: string;
  user_id: string;
}

export interface HomeworkCreatePayload {
  title: string;
  description?: string;
  subject?: string;
  due_date?: string; // ISO string
  assigned_to: string;
  created_by?: string;
}

export async function fetchHomeworks(userId?: string) {
  const resp = await api.get<Homework[]>('/homeworks', {
    params: userId ? { user_id: userId } : undefined,
  });
  return resp.data;
}

export async function submitHomework(homeworkId: number, payload: HomeworkSubmissionPayload) {
  const resp = await api.post(`/homeworks/${homeworkId}/submit`, payload);
  return resp.data;
}

export async function createHomework(payload: HomeworkCreatePayload) {
  const resp = await api.post<Homework>('/homeworks', payload);
  return resp.data;
}

