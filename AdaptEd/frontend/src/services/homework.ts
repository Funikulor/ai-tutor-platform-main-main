import api from './api';

export interface Homework {
  id: number;
  title: string;
  description?: string;
  subject?: string;
  due_date?: string;
  kind?: string;
  test_id?: number;
  assignment_type?: 'homework' | 'control' | 'quiz';
  status: string;
  assigned_to: string;
  created_by?: string;
  created_at: string;
  latest_submission_id?: number;
  latest_test_submission_id?: number;
}

export interface HomeworkSubmissionPayload {
  answer_text?: string;
  user_id: string;
  test_submission_id?: number;
}

export interface HomeworkCreatePayload {
  title: string;
  description?: string;
  subject?: string;
  due_date?: string; // ISO string
  kind?: string;
  test_id?: number;
  assignment_type?: 'homework' | 'control' | 'quiz';
  assigned_to: string;
  created_by?: string;
}

export interface AssignedHomeworkQuestionUpdate {
  question: string;
  options: string[];
  correct_index: number;
  question_type?: 'single' | 'multiple' | 'text' | 'numeric';
  correct_answer?: string | number | string[] | number[];
  explanation?: string;
  points?: number;
}

export interface AssignedHomeworkUpdatePayload {
  title?: string;
  topic?: string;
  difficulty?: string;
  questions?: AssignedHomeworkQuestionUpdate[];
  due_date?: string;
  assignment_type?: 'homework' | 'control' | 'quiz';
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

export async function updateAssignedHomework(homeworkId: number, payload: AssignedHomeworkUpdatePayload) {
  const resp = await api.put(`/teacher/homeworks/${homeworkId}`, payload);
  return resp.data;
}

export async function deleteAssignedHomework(homeworkId: number) {
  const resp = await api.delete(`/teacher/homeworks/${homeworkId}`);
  return resp.data;
}

