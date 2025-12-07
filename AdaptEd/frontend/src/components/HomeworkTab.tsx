import { useEffect, useState } from 'react';
import { fetchHomeworks, submitHomework, Homework } from '../services/homework';
import { CheckCircle, Clock, Loader2, Send, BookOpen } from 'lucide-react';

function statusLabel(status: string) {
  switch (status) {
    case 'new':
      return 'Новое';
    case 'in_progress':
      return 'В процессе';
    case 'submitted':
      return 'Отправлено';
    case 'checked':
      return 'Проверено';
    default:
      return status;
  }
}

function statusColor(status: string) {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-700';
    case 'in_progress':
      return 'bg-amber-100 text-amber-700';
    case 'submitted':
      return 'bg-purple-100 text-purple-700';
    case 'checked':
      return 'bg-green-100 text-green-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export function HomeworkTab() {
  const [homeworks, setHomeworks] = useState<Homework[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const userId = localStorage.getItem('user_id') || 'student';

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHomeworks(userId);
      setHomeworks(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Не удалось загрузить домашки');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (hw: Homework) => {
    if (!answers[hw.id]?.trim()) return;
    setSubmitLoading(hw.id);
    setError(null);
    try {
      await submitHomework(hw.id, { user_id: userId, answer_text: answers[hw.id] });
      await load();
      setAnswers((prev) => ({ ...prev, [hw.id]: '' }));
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Не удалось отправить ответ');
    } finally {
      setSubmitLoading(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-blue-600" />
          <h2 className="text-lg font-semibold text-gray-900">Мои домашние задания</h2>
        </div>
        <button
          onClick={load}
          className="px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
          disabled={loading}
        >
          Обновить
        </button>
      </div>

      {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}

      {loading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="w-4 h-4 animate-spin" />
          Загружаем домашние задания...
        </div>
      )}

      {!loading && homeworks.length === 0 && (
        <div className="p-4 bg-white border border-dashed border-gray-300 rounded-lg text-gray-600 text-sm">
          Домашних заданий пока нет.
        </div>
      )}

      <div className="space-y-4">
        {homeworks.map((hw) => (
          <div key={hw.id} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-gray-500">{hw.subject || 'Домашка'}</p>
                <h3 className="text-lg font-semibold text-gray-900">{hw.title}</h3>
                {hw.due_date && (
                  <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                    <Clock className="w-4 h-4" />
                    Дедлайн: {new Date(hw.due_date).toLocaleDateString('ru-RU')}
                  </div>
                )}
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor(hw.status)}`}>
                {statusLabel(hw.status)}
              </span>
            </div>

            {hw.description && <p className="text-sm text-gray-700 mt-2">{hw.description}</p>}

            <div className="mt-4 space-y-2">
              <textarea
                value={answers[hw.id] || ''}
                onChange={(e) => setAnswers((prev) => ({ ...prev, [hw.id]: e.target.value }))}
                placeholder="Ваш ответ..."
                className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                disabled={submitLoading === hw.id}
              />
              <div className="flex items-center justify-between">
                <button
                  onClick={() => handleSubmit(hw)}
                  disabled={submitLoading === hw.id || !answers[hw.id]?.trim()}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg disabled:opacity-50 hover:bg-blue-700 transition"
                >
                  {submitLoading === hw.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                  Отправить
                </button>
                {hw.status === 'submitted' && (
                  <div className="flex items-center gap-1 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Отправлено
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}






