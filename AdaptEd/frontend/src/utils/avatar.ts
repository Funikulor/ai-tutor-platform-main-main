const DICEBEAR = 'https://api.dicebear.com/7.x/avataaars/svg';

/**
 * URL аватара по seed (DiceBear Avataaars). Для пользователей без seed возвращает null.
 */
export function getAvatarUrl(seed: string | null | undefined): string | null {
  if (!seed || typeof seed !== 'string') return null;
  return `${DICEBEAR}?seed=${encodeURIComponent(seed)}`;
}

/** Генерирует новый случайный seed для аватара */
export function randomAvatarSeed(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}
