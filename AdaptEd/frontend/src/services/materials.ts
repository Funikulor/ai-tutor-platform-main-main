import api from './api';
import type { Material } from '../components/LibraryTab';

export async function fetchMaterials(params?: {
  subject?: string;
  material_type?: 'all' | 'article' | 'video' | 'pdf';
  q?: string;
}) {
  const { data } = await api.get<Material[]>('/materials', { params });
  return data;
}

