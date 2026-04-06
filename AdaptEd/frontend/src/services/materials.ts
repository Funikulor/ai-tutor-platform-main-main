import api from './api';
import type { Material } from '../components/LibraryTab';

/** Публичные поля контрольного вопроса (без правильных ответов) */
export interface LibraryLessonCheckpoint {
  question: string;
  type: 'single_choice' | 'numeric' | 'short_text';
  options?: string[];
}

export interface LibraryLesson {
  id: string;
  title: string;
  content: string;
  checkpoint: LibraryLessonCheckpoint;
}

export interface LibraryCourse {
  id: string;
  title: string;
  description: string;
  subject: string;
  topic: string;
  difficulty: string;
  estimated_minutes?: number;
  lessons: LibraryLesson[];
}

export async function fetchMaterials(params?: {
  subject?: string;
  material_type?: 'all' | 'article' | 'video' | 'pdf';
  q?: string;
}) {
  const { data } = await api.get<Material[]>('/materials', { params });
  return data;
}

export async function fetchLibraryCourses(): Promise<LibraryCourse[]> {
  const { data } = await api.get<LibraryCourse[]>('/library/courses');
  return Array.isArray(data) ? data : [];
}

/** Полный checkpoint для админ-редактора (включая правильные ответы) */
export interface AdminLibraryCheckpoint {
  type?: string;
  question?: string;
  options?: string[];
  correct_index?: number;
  correct_answer?: string;
  acceptable_answers?: string[];
}

export interface AdminLibraryLessonFull {
  id: string;
  title: string;
  content?: string;
  checkpoint?: AdminLibraryCheckpoint;
}

export interface AdminLibraryCourseFull {
  id: string;
  title: string;
  description?: string;
  subject?: string;
  topic?: string;
  difficulty?: string;
  estimated_minutes?: number;
  lessons: AdminLibraryLessonFull[];
}

export async function fetchAdminLibraryCourse(courseId: string): Promise<AdminLibraryCourseFull> {
  const { data } = await api.get<AdminLibraryCourseFull>(`/admin/library/courses/${encodeURIComponent(courseId)}`);
  return data;
}

export async function saveAdminLibraryCourse(course: AdminLibraryCourseFull): Promise<void> {
  await api.post('/admin/library/courses', course as Record<string, unknown>);
}

export async function putLibraryMaterial(
  materialId: string,
  patch: Partial<{
    title: string;
    description: string;
    content: string;
    subject: string;
    topic: string;
    type: string;
    difficulty: string;
    duration: string;
  }>
): Promise<void> {
  await api.put(`/admin/library/materials/${encodeURIComponent(materialId)}`, patch);
}

export async function createLibraryMaterial(body: {
  title: string;
  description?: string;
  content?: string;
  subject?: string;
  topic?: string;
  type?: string;
  difficulty?: string;
  duration?: string;
}): Promise<{ id: string; material: Record<string, unknown> }> {
  const { data } = await api.post<{ id: string; material: Record<string, unknown> }>(
    '/admin/library/materials',
    body
  );
  return data;
}

export async function deleteAdminLibraryCourse(courseId: string): Promise<void> {
  await api.delete(`/admin/library/courses/${encodeURIComponent(courseId)}`);
}

/** Карточка материала в обзоре программы (как в пикере; полного content может не быть) */
export interface CurriculumMaterialCard {
  id: string;
  title: string;
  description: string;
  subject: string;
  topic: string;
  type: string;
  difficulty: string;
  duration?: string;
  rating?: number;
}

export interface CurriculumProgramTopic {
  id: number;
  name: string;
  description: string;
  grade_hint: string;
  materials: CurriculumMaterialCard[];
  courses: LibraryCourse[];
}

export interface CurriculumProgramSection {
  id: number;
  name: string;
  topics: CurriculumProgramTopic[];
}

export interface CurriculumProgramSubject {
  id: number;
  subject: string;
  sections: CurriculumProgramSection[];
}

export async function fetchCurriculumOverview(): Promise<CurriculumProgramSubject[]> {
  const { data } = await api.get<{ subjects: CurriculumProgramSubject[] }>(
    '/library/curriculum-overview'
  );
  return Array.isArray(data?.subjects) ? data.subjects : [];
}

