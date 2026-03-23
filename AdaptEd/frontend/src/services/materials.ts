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

