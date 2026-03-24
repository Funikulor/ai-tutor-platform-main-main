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

