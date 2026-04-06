import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Loader2, Check } from 'lucide-react';
import type { Material } from './LibraryTab';
import { putLibraryMaterial } from '../services/materials';
import { toast } from 'sonner';

interface MaterialAdminEditorProps {
  material: Material;
  onBack: () => void;
  onSaved: () => void;
}

export function MaterialAdminEditor({ material, onBack, onSaved }: MaterialAdminEditorProps) {
  const [title, setTitle] = useState(material.title);
  const [description, setDescription] = useState(material.description);
  const [content, setContent] = useState(material.content || '');
  const [subject, setSubject] = useState(material.subject);
  const [topic, setTopic] = useState(material.topic);
  const [type, setType] = useState(material.type);
  const [difficulty, setDifficulty] = useState(material.difficulty);
  const [duration, setDuration] = useState(material.duration || '');
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const skipRef = useRef(true);
  const onSavedRef = useRef(onSaved);
  onSavedRef.current = onSaved;

  useEffect(() => {
    setTitle(material.title);
    setDescription(material.description);
    setContent(material.content || '');
    setSubject(material.subject);
    setTopic(material.topic);
    setType(material.type);
    setDifficulty(material.difficulty);
    setDuration(material.duration || '');
    skipRef.current = true;
  }, [material.id]);

  useEffect(() => {
    const t = setTimeout(() => {
      void (async () => {
        if (skipRef.current) {
          skipRef.current = false;
          return;
        }
        if (!title.trim()) return;
        setSaveState('saving');
        try {
          await putLibraryMaterial(material.id, {
            title: title.trim(),
            description,
            content,
            subject,
            topic,
            type,
            difficulty,
            duration,
          });
          setSaveState('saved');
          onSavedRef.current();
        } catch (e: unknown) {
          console.error(e);
          setSaveState('error');
          toast.error('Не удалось сохранить материал');
        }
      })();
    }, 850);
    return () => clearTimeout(t);
  }, [title, description, content, subject, topic, type, difficulty, duration, material.id]);

  useEffect(() => {
    if (saveState !== 'saved') return;
    const u = setTimeout(() => setSaveState('idle'), 2000);
    return () => clearTimeout(u);
  }, [saveState]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-200 pb-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm font-medium text-indigo-700 hover:text-indigo-900"
        >
          <ArrowLeft className="h-4 w-4" />
          К списку материалов
        </button>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          {saveState === 'saving' && (
            <>
              <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
              Сохранение…
            </>
          )}
          {saveState === 'saved' && (
            <>
              <Check className="h-4 w-4 text-emerald-600" />
              Сохранено
            </>
          )}
          {saveState === 'error' && <span className="text-rose-600">Ошибка сохранения</span>}
          {saveState === 'idle' && <span className="text-gray-400">Изменения сохраняются автоматически</span>}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block md:col-span-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Название</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block md:col-span-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Краткое описание</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Предмет</span>
          <input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Тема (тег)</span>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Тип</span>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as Material['type'])}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="article">Статья</option>
            <option value="video">Видео</option>
            <option value="pdf">PDF</option>
          </select>
        </label>
        <label className="block">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Сложность</span>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as Material['difficulty'])}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="beginner">Начальный</option>
            <option value="intermediate">Средний</option>
            <option value="advanced">Продвинутый</option>
          </select>
        </label>
        <label className="block md:col-span-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">Длительность (подпись)</span>
          <input
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            placeholder="15 мин"
          />
        </label>
        <label className="block md:col-span-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Текст (Markdown для статей; для видео/PDF можно вставить ссылки)
          </span>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={16}
            className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm"
          />
        </label>
      </div>
    </div>
  );
}
