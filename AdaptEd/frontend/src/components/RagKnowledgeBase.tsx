import { useEffect, useState } from 'react';
import { Database, BookUp, Sparkles, Loader2, Search, FileText, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import api from '../services/api';

interface RagSource {
  source: string;
  chunks: number;
}

interface RagStatus {
  embeddings_available: boolean;
  embeddings_model: string;
  indexed_chunks: number;
  sources: RagSource[];
}

interface ClassifyMatch {
  topic: string;
  score: number;
  source: string;
  text: string;
}

export function RagKnowledgeBase() {
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [seeding, setSeeding] = useState(false);

  // Загрузка учебника
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfTopic, setPdfTopic] = useState('');
  const [uploadingPdf, setUploadingPdf] = useState(false);

  const [textTitle, setTextTitle] = useState('');
  const [textTopic, setTextTopic] = useState('');
  const [textContent, setTextContent] = useState('');
  const [savingText, setSavingText] = useState(false);

  // Проверка классификации
  const [testQuestion, setTestQuestion] = useState('');
  const [classifying, setClassifying] = useState(false);
  const [matches, setMatches] = useState<ClassifyMatch[]>([]);

  // Управление индексом
  const [deletingSource, setDeletingSource] = useState<string | null>(null);
  const [clearingAll, setClearingAll] = useState(false);

  const loadStatus = async () => {
    setLoadingStatus(true);
    try {
      const { data } = await api.get<RagStatus>('/rag/status');
      setStatus(data);
    } catch {
      toast.error('Не удалось получить статус базы знаний');
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleSeedTopics = async () => {
    setSeeding(true);
    try {
      const { data } = await api.post('/rag/ingest-topics', {});
      toast.success(`Темы добавлены: ${data.added}`);
      await loadStatus();
    } catch {
      toast.error('Не удалось засеять темы (проверьте ключ эмбеддингов)');
    } finally {
      setSeeding(false);
    }
  };

  const handleUploadPdf = async () => {
    if (!pdfFile) {
      toast.error('Выберите PDF-файл');
      return;
    }
    setUploadingPdf(true);
    try {
      const form = new FormData();
      form.append('file', pdfFile);
      if (pdfTopic.trim()) form.append('topic_hint', pdfTopic.trim());
      const { data } = await api.post('/rag/ingest-pdf', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      });
      toast.success(`Учебник проиндексирован: фрагментов ${data.added}`);
      setPdfFile(null);
      setPdfTopic('');
      await loadStatus();
    } catch {
      toast.error('Не удалось загрузить PDF');
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleSaveText = async () => {
    if (!textTitle.trim() || !textContent.trim()) {
      toast.error('Заполните название и текст');
      return;
    }
    setSavingText(true);
    try {
      const { data } = await api.post('/rag/ingest-text', {
        title: textTitle.trim(),
        content: textContent.trim(),
        topic_hint: textTopic.trim() || undefined,
      });
      toast.success(`Текст проиндексирован: фрагментов ${data.added}`);
      setTextTitle('');
      setTextTopic('');
      setTextContent('');
      await loadStatus();
    } catch {
      toast.error('Не удалось сохранить текст');
    } finally {
      setSavingText(false);
    }
  };

  const handleDeleteSource = async (source: string) => {
    if (!window.confirm(`Удалить источник «${source}» из базы знаний?`)) return;
    setDeletingSource(source);
    try {
      const { data } = await api.delete('/rag/source', { params: { source } });
      toast.success(`Удалено фрагментов: ${data.deleted}`);
      await loadStatus();
    } catch {
      toast.error('Не удалось удалить источник');
    } finally {
      setDeletingSource(null);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Полностью очистить индекс базы знаний? Это удалит все темы и учебники.')) return;
    setClearingAll(true);
    try {
      const { data } = await api.delete('/rag/all');
      toast.success(`Индекс очищен: удалено ${data.deleted}`);
      setMatches([]);
      await loadStatus();
    } catch {
      toast.error('Не удалось очистить индекс');
    } finally {
      setClearingAll(false);
    }
  };

  const handleClassify = async () => {
    if (!testQuestion.trim()) return;
    setClassifying(true);
    try {
      const { data } = await api.get('/rag/classify', { params: { question: testQuestion.trim() } });
      setMatches(data.matches || []);
    } catch {
      toast.error('Не удалось классифицировать');
    } finally {
      setClassifying(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Статус */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-slate-900">База знаний (RAG)</h3>
              <p className="mt-1 text-sm text-slate-600">
                Семантическое определение тем и контекст для подсказок. Загрузите учебник, чтобы система
                сопоставляла задачи с реальными разделами.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={loadStatus}
            disabled={loadingStatus}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            {loadingStatus ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Обновить
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3">
            <div className="text-xs text-slate-500">Эмбеддинги</div>
            <div className={`mt-1 text-sm font-semibold ${status?.embeddings_available ? 'text-emerald-600' : 'text-rose-600'}`}>
              {status?.embeddings_available ? 'Доступны' : 'Недоступны'}
            </div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3">
            <div className="text-xs text-slate-500">Модель</div>
            <div className="mt-1 text-sm font-semibold text-slate-800">{status?.embeddings_model || '—'}</div>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-3">
            <div className="text-xs text-slate-500">Фрагментов в индексе</div>
            <div className="mt-1 text-sm font-semibold text-slate-800">{status?.indexed_chunks ?? '—'}</div>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleSeedTopics}
            disabled={seeding}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {seeding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Засеять базовые темы (школьная математика)
          </button>
          <button
            type="button"
            onClick={handleClearAll}
            disabled={clearingAll || !status?.indexed_chunks}
            className="inline-flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-medium text-rose-700 transition hover:bg-rose-100 disabled:opacity-50"
          >
            {clearingAll ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            Очистить индекс
          </button>
        </div>

        {status?.sources && status.sources.length > 0 && (
          <div className="mt-4">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Источники в индексе</div>
            <div className="space-y-2">
              {status.sources.map((s) => (
                <div
                  key={s.source}
                  className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/60 px-4 py-2.5 text-sm"
                >
                  <div className="min-w-0">
                    <span className="truncate font-medium text-slate-800">{s.source}</span>
                    <span className="ml-2 text-xs text-slate-500">фрагментов: {s.chunks}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteSource(s.source)}
                    disabled={deletingSource === s.source}
                    className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-rose-600 transition hover:bg-rose-50 disabled:opacity-50"
                  >
                    {deletingSource === s.source ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="h-3.5 w-3.5" />
                    )}
                    Удалить
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Загрузка учебника */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center gap-2 text-slate-900">
            <BookUp className="h-5 w-5 text-emerald-600" />
            <h4 className="font-semibold">Загрузить учебник (PDF)</h4>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            PDF разбивается на фрагменты, каждый превращается в вектор и сохраняется в базу знаний.
          </p>
          <div className="mt-4 space-y-3">
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-emerald-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-emerald-700 hover:file:bg-emerald-100"
            />
            <input
              type="text"
              value={pdfTopic}
              onChange={(e) => setPdfTopic(e.target.value)}
              placeholder="Тема/раздел (необязательно), напр. «Квадратные уравнения»"
              className="w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 focus:border-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
            <button
              type="button"
              onClick={handleUploadPdf}
              disabled={uploadingPdf}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-60"
            >
              {uploadingPdf ? <Loader2 className="h-4 w-4 animate-spin" /> : <BookUp className="h-4 w-4" />}
              Загрузить и проиндексировать
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
          <div className="flex items-center gap-2 text-slate-900">
            <FileText className="h-5 w-5 text-teal-600" />
            <h4 className="font-semibold">Добавить текст вручную</h4>
          </div>
          <p className="mt-1 text-sm text-slate-600">Вставьте фрагмент конспекта или раздела учебника.</p>
          <div className="mt-4 space-y-3">
            <input
              type="text"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Название источника"
              className="w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 focus:border-teal-300 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            />
            <input
              type="text"
              value={textTopic}
              onChange={(e) => setTextTopic(e.target.value)}
              placeholder="Тема (необязательно)"
              className="w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 focus:border-teal-300 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            />
            <textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Текст раздела..."
              rows={4}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 focus:border-teal-300 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            />
            <button
              type="button"
              onClick={handleSaveText}
              disabled={savingText}
              className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-60"
            >
              {savingText ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Сохранить в базу знаний
            </button>
          </div>
        </div>
      </div>

      {/* Проверка классификации */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex items-center gap-2 text-slate-900">
          <Search className="h-5 w-5 text-violet-600" />
          <h4 className="font-semibold">Проверить определение темы</h4>
        </div>
        <p className="mt-1 text-sm text-slate-600">Введите условие задачи — система покажет ближайшие темы.</p>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <input
            type="text"
            value={testQuestion}
            onChange={(e) => setTestQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleClassify()}
            placeholder="Напр. «Решите неравенство 2x+1<5»"
            className="flex-1 rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm text-slate-800 focus:border-violet-300 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
          />
          <button
            type="button"
            onClick={handleClassify}
            disabled={classifying}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-violet-700 disabled:opacity-60"
          >
            {classifying ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            Определить
          </button>
        </div>
        {matches.length > 0 && (
          <div className="mt-4 space-y-2">
            {matches.map((m, i) => (
              <div
                key={i}
                className={`flex items-center justify-between rounded-xl border px-4 py-2.5 text-sm ${
                  i === 0 ? 'border-violet-200 bg-violet-50/60' : 'border-slate-100 bg-slate-50/60'
                }`}
              >
                <div>
                  <span className="font-medium text-slate-900">{m.topic}</span>
                  <span className="ml-2 text-xs text-slate-500">источник: {m.source}</span>
                </div>
                <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
                  {(m.score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default RagKnowledgeBase;
