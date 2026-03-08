import api from './api';

export interface ManualQuestion {
  question: string;
  options: string[];
  correct_index: number;
  question_type?: 'single' | 'multiple' | 'text' | 'numeric';
  correct_answer?: string | number | string[] | number[];
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
  correct_answer?: string | number | string[] | number[];
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
  const { data } = await api.put<{ test?: TestDetail } & TestDetail>(`/tests/${id}`, payload);
  return data.test || (data as TestDetail);
}

export async function deleteTest(id: number) {
  const { data } = await api.delete<{ ok: boolean }>(`/tests/${id}`);
  return data;
}

export async function assignTestAsHomework(
  testId: number,
  studentIds: string[],
  dueDate?: string,
  assignmentType: 'homework' | 'control' | 'quiz' = 'homework'
) {
  const { data } = await api.post<{ success: boolean; homeworks: any[]; assigned_count: number }>('/tests/assign', {
    test_id: testId,
    student_ids: studentIds,
    assignment_type: assignmentType,
    due_date: dueDate,
    created_by: localStorage.getItem('user_id') || undefined,
  });
  return data;
}

export interface SubmittedAnswerPayload {
  question_id?: number;
  selected_option_indexes?: number[];
  answer_text?: string;
  answer_number?: number;
  student_explanation?: string;
}

export interface QuestionResult {
  question_id: number;
  question: string;
  question_type: 'single' | 'multiple' | 'text' | 'numeric';
  selected_option_indexes?: number[];
  selected_option_texts?: string[];
  student_answer?: string | number | string[] | number[];
  student_explanation?: string;
  is_correct: boolean;
  correct_answer?: string | number | string[] | number[];
  correct_answer_text?: string;
  question_explanation?: string;
}

export interface TestSubmissionSummary {
  id: number;
  user_id: string;
  homework_id?: number;
  score: number;
  correct_count?: number;
  total_questions?: number;
  summary?: string;
  feedback?: string;
  created_at?: string;
}

export interface TestSubmissionDetail extends TestSubmissionSummary {
  test_id: number;
  answers: SubmittedAnswerPayload[];
  question_results: QuestionResult[];
  test?: TestDetail;
}

export async function submitTest(
  testId: number,
  payload: {
    user_id: string;
    homework_id?: number;
    time_spent_seconds?: number;
    answers: SubmittedAnswerPayload[];
  }
) {
  const { data } = await api.post<{
    submission_id: number;
    homework_id?: number;
    score: number;
    correct: number;
    total: number;
    summary?: string;
    feedback?: string;
    question_results: QuestionResult[];
  }>(`/tests/${testId}/submit`, {
    ...payload,
  });
  return data;
}

export async function listTestSubmissions(testId: number) {
  const { data } = await api.get<TestSubmissionSummary[]>(`/tests/${testId}/submissions`);
  return data;
}

export async function getTestSubmission(submissionId: number) {
  const { data } = await api.get<TestSubmissionDetail>(`/tests/submissions/${submissionId}`);
  return data;
}

