/**
 * PNG надёжнее отображается в <img>, чем SVG (object-fit, блокировщики, масштаб).
 * @see https://www.dicebear.com/how-to-use/http-api/
 */
export function getAvatarUrl(seed: string | null | undefined, sizePx: number = 128): string | null {
  if (!seed || typeof seed !== 'string') return null;
  const size = Math.min(512, Math.max(32, Math.round(sizePx)));
  return `https://api.dicebear.com/7.x/avataaars/png?seed=${encodeURIComponent(seed)}&size=${size}`;
}

/** Первая видимая буква имени для аватара-плейсхолдера (кириллица/Latin). */
export function avatarInitial(name: string | null | undefined): string {
  const s = String(name ?? '')
    .trim()
    .replace(/^\uFEFF/, '');
  if (!s) return '?';
  return s.charAt(0).toLocaleUpperCase('ru-RU');
}

/** Генерирует новый случайный seed для аватара */
export function randomAvatarSeed(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}
