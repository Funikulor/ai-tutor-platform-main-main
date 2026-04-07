import { useState, useEffect, useRef, useCallback, useLayoutEffect, type ReactElement } from 'react';
import { ArrowLeft, BookOpen, Video, FileText, Clock, Star, Download, Share2, CheckCircle, Target, Lightbulb, AlertCircle, Zap } from 'lucide-react';
import { motion } from 'motion/react';
import type { Material } from './LibraryTab';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { toast } from 'sonner';

// Функция для форматирования математических формул (скопирована из AdaptiveTask)
const formatMathText = (text: string): ReactElement[] => {
  let cleaned = text
    .replace(/\\\(/g, '')
    .replace(/\\\)/g, '')
    .replace(/\\\[/g, '')
    .replace(/\\\]/g, '')
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '($1)/($2)')
    .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
    .replace(/\\sqrt\[([^\]]+)\]\{([^}]+)\}/g, 'корень $1 степени из ($2)')
    .replace(/\^\{([^}]+)\}/g, '^$1')
    // Обрабатываем степени вида ^2, ^3 и т.д.
    .replace(/\^(\d+)/g, (_match, num) => {
      const superscripts: { [key: string]: string } = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
      };
      return superscripts[num] || `^${num}`;
    })
    // Обрабатываем степени, написанные напрямую как обычные символы (если они уже есть в тексте)
    // Это не нужно, так как они уже правильные
    .replace(/\{|\}/g, '')
    .replace(/(\d+|\w+)\s*\*\s*(\d+|\w+)/g, (match, left, right, offset, string) => {
      const before = offset > 0 ? string[offset - 1] : ' ';
      const after = offset + match.length < string.length ? string[offset + match.length] : ' ';
      if (before === ':' || after === ':') {
        return match;
      }
      return `${left} · ${right}`;
    });

  // Обрабатываем дроби вида: (-b ± √D) / 2a
  cleaned = cleaned.replace(/(\([^)]+\))\s*\/\s*(\d+[a-zA-Z]?|[a-zA-Z]+\d*)/g, (_match, numerator, denominator) => {
    return `(${numerator.slice(1, -1)})/${denominator}`;
  });

  // Обрабатываем дроби без скобок в числителе: -b ± √D / 2a
  cleaned = cleaned.replace(/([a-zA-Z0-9±√\s()]+)\s*\/\s*(\d+[a-zA-Z]?|[a-zA-Z]+\d*)/g, (match, numerator, denominator, offset, string) => {
    // Проверяем контекст - это должна быть отдельная формула
    const before = offset > 0 ? string.substring(Math.max(0, offset - 10), offset) : '';
    const after = offset + match.length < string.length ? string.substring(offset + match.length, Math.min(string.length, offset + match.length + 10)) : '';
    
    // Если перед этим есть знак =, : или начало строки, и после есть пробел, =, или конец - это дробь
    if ((/[=:\s]|^/.test(before.slice(-1)) || before.trim() === '') && 
        (/[\s=,\n]|$/.test(after.charAt(0)) || after.trim() === '')) {
      // Если числитель не в скобках и содержит операции, добавляем скобки
      if (!numerator.trim().startsWith('(') && /[+\-±√]/.test(numerator)) {
        return `(${numerator.trim()})/${denominator}`;
      }
      return match;
    }
    return match;
  });

  const parts: (string | ReactElement)[] = [];
  let lastIndex = 0;

  const fractionPattern = /(\([^()]+\)|[a-zA-Z]?\d+[a-zA-Z]*|\d+)\s*\/\s*(\([^()]+\)|[a-zA-Z]?\d+[a-zA-Z]*|\d+)/g;
  const matches: Array<{index: number, length: number, numerator: string, denominator: string}> = [];
  let match: RegExpExecArray | null;

  while ((match = fractionPattern.exec(cleaned)) !== null) {
    let numerator = match[1].trim();
    let denominator = match[2].trim();

    const beforeChar = match.index > 0 ? cleaned[match.index - 1] : ' ';
    const afterChar = match.index + match[0].length < cleaned.length
      ? cleaned[match.index + match[0].length]
      : ' ';

    if (beforeChar === ':' || afterChar === ':') {
      continue;
    }

    if (numerator.startsWith('(') && numerator.endsWith(')')) {
      numerator = numerator.slice(1, -1).trim();
    }
    if (denominator.startsWith('(') && denominator.endsWith(')')) {
      denominator = denominator.slice(1, -1).trim();
    }

    if (numerator && denominator) {
      const overlaps = matches.some(m => {
        const matchStart = match!.index;
        const matchEnd = match!.index + match![0].length;
        const mStart = m.index;
        const mEnd = m.index + m.length;
        return (matchStart >= mStart && matchStart < mEnd) ||
               (mStart >= matchStart && mStart < matchEnd);
      });

      if (!overlaps) {
        matches.push({
          index: match.index,
          length: match[0].length,
          numerator: numerator,
          denominator: denominator
        });
      }
    }
  }

  // Убираем автоматическое выделение чисел - оставляем только дроби
  // Числа не выделяем жирным, чтобы не портить читаемость
  const allElements = [
    ...matches.map(m => ({ ...m, type: 'fraction' as const }))
  ].sort((a, b) => a.index - b.index);

  if (allElements.length === 0) {
    return [<span key="text">{cleaned}</span>];
  }

  allElements.forEach((element, idx) => {
    if (element.index > lastIndex) {
      parts.push(cleaned.substring(lastIndex, element.index));
    }

    if (element.type === 'fraction') {
      const frac = element as typeof matches[0];
      parts.push(
        <span
          key={`frac-${idx}`}
          className="inline-flex flex-col items-center mx-1 my-0.5"
          style={{
            verticalAlign: 'middle',
            lineHeight: '1.2',
            fontSize: '1em',
            display: 'inline-flex'
          }}
        >
          <span
            className="text-base leading-none border-b-2 border-gray-800 pb-0.5 px-1 font-semibold text-center"
            style={{ minHeight: '1.2em', display: 'block', fontWeight: '600' }}
          >
            {frac.numerator}
          </span>
          <span
            className="text-base leading-none mt-0.5 px-1 text-center font-semibold"
            style={{ minHeight: '1.2em', display: 'block', fontWeight: '600' }}
          >
            {frac.denominator}
          </span>
        </span>
      );
      lastIndex = frac.index + frac.length;
    }
  });

  if (lastIndex < cleaned.length) {
    parts.push(cleaned.substring(lastIndex));
  }

  // Обрабатываем степени в финальном результате - заменяем обычные символы на верхние индексы
  const processedParts = parts.map((part, index) => {
    if (typeof part === 'string') {
      // Заменяем обычные цифры после переменных на верхние индексы
      // Например: c2 -> c², a2 -> a², но не трогаем числа отдельно
      const processed = part.replace(/([a-zA-Z])(\d)/g, (_match, letter, digit) => {
        const superscripts: { [key: string]: string } = {
          '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
          '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
        };
        return letter + (superscripts[digit] || digit);
      });
      return <span key={`text-${index}`}>{processed}</span>;
    }
    return part;
  });

  return processedParts;
};

interface MaterialViewerProps {
  material: Material;
  onBack: () => void;
  onStudyComplete?: (topic: string) => void;
  allMaterials?: Material[];
  onSelectRelated?: (material: Material) => void;
}

/** Короткий текст без прокрутки: засчитываем после N секунд на странице (не мгновенно при открытии). */
const NO_SCROLL_DWELL_SECONDS = 20;
/** Длинный текст: достаточно прокрутить почти до конца. */
const SCROLL_COMPLETE_PCT = 95;

export function MaterialViewer({ material, onBack, onStudyComplete, allMaterials = [], onSelectRelated }: MaterialViewerProps) {
  const [timeSpent, setTimeSpent] = useState(0);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [noScrollNeeded, setNoScrollNeeded] = useState(false);
  const [isStudied, setIsStudied] = useState(false);
  const [isMarking, setIsMarking] = useState(false);
  const startTimeRef = useRef<number>(Date.now());
  const contentRef = useRef<HTMLDivElement>(null);
  /** Защита от повторной отправки / двойного срабатывания эффектов */
  const studySentRef = useRef(false);

  // Сброс при смене материала
  useEffect(() => {
    startTimeRef.current = Date.now();
    studySentRef.current = false;
    setIsStudied(false);
    setScrollProgress(0);
    setNoScrollNeeded(false);
    setTimeSpent(0);
  }, [material.id]);

  // Время на странице (для коротких материалов и отображения)
  useEffect(() => {
    const tick = () => setTimeSpent(Math.floor((Date.now() - startTimeRef.current) / 1000));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [material.id]);

  const measureScroll = useCallback(() => {
    const el = contentRef.current;
    if (!el) return;
    const maxScroll = el.scrollHeight - el.clientHeight;
    const shortContent = maxScroll <= 4;
    setNoScrollNeeded(shortContent);
    if (shortContent) {
      setScrollProgress(100);
      return;
    }
    const scrollTop = el.scrollTop;
    const progress = maxScroll > 0 ? (scrollTop / maxScroll) * 100 : 0;
    setScrollProgress(Math.min(100, Math.max(0, progress)));
  }, []);

  useLayoutEffect(() => {
    measureScroll();
    const el = contentRef.current;
    if (!el) return;
    el.addEventListener('scroll', measureScroll);
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => measureScroll()) : null;
    if (ro) ro.observe(el);
    const t = window.setTimeout(measureScroll, 100);
    const t2 = window.setTimeout(measureScroll, 500);
    return () => {
      el.removeEventListener('scroll', measureScroll);
      ro?.disconnect();
      window.clearTimeout(t);
      window.clearTimeout(t2);
    };
  }, [material.id, material.content, material.type, measureScroll]);

  const handleMarkAsStudied = useCallback(
    async (completionFraction: number) => {
      if (studySentRef.current) return;
      studySentRef.current = true;
      try {
        setIsMarking(true);
        const userId = localStorage.getItem('user_id');
        if (!userId) {
          throw new Error('User ID not found');
        }
        const currentTimeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);
        setTimeSpent(currentTimeSpent);

        const topicLabel = (material.topic || material.title || material.subject || 'Материалы').trim();
        const response = await api.post('/study/material', {
          user_id: userId,
          material_id: material.id,
          topic: topicLabel,
          subject: material.subject,
          time_spent_seconds: currentTimeSpent,
          completion_percentage: Math.min(1, Math.max(0, completionFraction)),
        });

        setIsStudied(true);

        if (onStudyComplete) {
          onStudyComplete(topicLabel);
        }

        toast.success(
          `Отлично! Материал по теме «${material.topic || topicLabel}» засчитан. Очков: ${response.data.points_earned ?? 0}.`,
          { duration: 4000 }
        );
      } catch (err: unknown) {
        studySentRef.current = false;
        console.error('Error marking material as studied:', err);
        toast.error('Не удалось отметить материал как изученный. Попробуйте ещё раз.', { duration: 4000 });
      } finally {
        setIsMarking(false);
      }
    },
    [material.id, material.topic, material.title, material.subject, onStudyComplete]
  );

  // Авто: прокрутка почти до конца
  useEffect(() => {
    if (noScrollNeeded) return;
    if (scrollProgress < SCROLL_COMPLETE_PCT || isStudied || isMarking) return;
    void handleMarkAsStudied(1);
  }, [scrollProgress, noScrollNeeded, isStudied, isMarking, handleMarkAsStudied]);

  // Авто: контент без прокрутки — после минимального времени на странице
  useEffect(() => {
    if (!noScrollNeeded || isStudied || isMarking) return;
    if (timeSpent < NO_SCROLL_DWELL_SECONDS) return;
    void handleMarkAsStudied(1);
  }, [noScrollNeeded, timeSpent, isStudied, isMarking, handleMarkAsStudied]);

  const dwellRemaining = Math.max(0, NO_SCROLL_DWELL_SECONDS - timeSpent);

  const handleShare = async () => {
    const shareData = {
      title: material.title,
      text: material.description,
      url: window.location.href,
    };

    try {
      if (navigator.share && navigator.canShare && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        toast.success('Материал успешно поделен!');
      } else {
        // Fallback: копируем ссылку в буфер обмена
        await navigator.clipboard.writeText(window.location.href);
        toast.success('Ссылка скопирована в буфер обмена!');
      }
    } catch (err: any) {
      // Пользователь отменил шаринг или произошла ошибка
      if (err.name !== 'AbortError') {
        // Пробуем fallback на копирование
        try {
          await navigator.clipboard.writeText(window.location.href);
          toast.success('Ссылка скопирована в буфер обмена!');
        } catch (clipboardErr) {
          toast.error('Не удалось поделиться материалом. Попробуйте скопировать ссылку вручную.');
        }
      }
    }
  };

  const handleDownloadPDF = () => {
    // Проверяем наличие PDF URL
    if (!material.pdfUrl) {
      toast.error('PDF файл недоступен для скачивания. Ссылка не найдена.');
      return;
    }

    try {
      // Открываем ссылку в новой вкладке для скачивания
      const link = document.createElement('a');
      link.href = material.pdfUrl;
      link.download = `${material.title.replace(/[^a-zа-яё0-9]/gi, '_')}.pdf`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer'; // Безопасность
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Начато скачивание PDF файла!');
    } catch (err) {
      console.error('Error downloading PDF:', err);
      // Fallback: открываем в новой вкладке
      try {
        window.open(material.pdfUrl, '_blank', 'noopener,noreferrer');
        toast.info('PDF файл открыт в новой вкладке.');
      } catch (openErr) {
        toast.error('Не удалось скачать PDF файл. Попробуйте открыть ссылку вручную.');
      }
    }
  };

  const getTypeIcon = () => {
    switch (material.type) {
      case 'video': return <Video className="w-6 h-6" />;
      case 'pdf': return <FileText className="w-6 h-6" />;
      default: return <BookOpen className="w-6 h-6" />;
    }
  };

  const getTypeColor = () => {
    switch (material.type) {
      case 'video': return 'from-red-500 to-pink-500';
      case 'pdf': return 'from-orange-500 to-amber-500';
      default: return 'from-blue-500 to-purple-600';
    }
  };

  const youtubeEmbedSrc = (raw?: string): string | null => {
    if (!raw?.trim()) return null;
    const u = raw.trim();
    if (u.includes('youtube.com/embed/')) return u;
    const m = u.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
    if (m) return `https://www.youtube.com/embed/${m[1]}?rel=0`;
    return u.startsWith('http') ? u : null;
  };

  const renderContent = () => {
    if (material.type === 'video') {
      const embed = youtubeEmbedSrc(material.videoUrl);
      return (
        <div className="space-y-6">
          {embed ? (
            <div className="rounded-xl overflow-hidden border border-gray-200 shadow-sm bg-black aspect-video">
              <iframe
                className="w-full h-full min-h-[200px]"
                src={embed}
                title={material.title}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
                loading="lazy"
                referrerPolicy="strict-origin-when-cross-origin"
              />
            </div>
          ) : (
            <div className="bg-gray-900 rounded-xl aspect-video flex items-center justify-center">
              <div className="text-center text-white px-4">
                <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-gray-400">Ссылка на видео не задана</p>
              </div>
            </div>
          )}
          <div className="prose max-w-none">
            <h2>О видеокурсе</h2>
            <p>{material.description}</p>
          </div>
        </div>
      );
    }

    if (material.type === 'pdf') {
      return (
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-12 border-2 border-orange-200">
            <div className="text-center">
              <FileText className="w-24 h-24 mx-auto mb-6 text-orange-500" />
              <h3 className="text-gray-900 text-xl mb-4">{material.title}</h3>
              <p className="text-gray-600 mb-6">{material.description}</p>
              <button 
                onClick={handleDownloadPDF}
                className="px-6 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-colors flex items-center gap-2 mx-auto"
              >
                <Download className="w-5 h-5" />
                Скачать PDF
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Article content with enhanced markdown rendering
    // Обрабатываем контент для форматирования формул
    const processContentForMath = (content: string): string => {
      // Обрабатываем формулы в тексте, особенно дроби вида (-b ± √D) / 2a
      // Заменяем их на специальный формат, который потом будет обработан
      return content
        .replace(/(\([^)]+\))\s*\/\s*(\d+[a-zA-Z]?|[a-zA-Z]+\d*)/g, (_match, num, den) => {
          // Убираем внешние скобки из числителя для обработки
          const numerator = num.startsWith('(') && num.endsWith(')') ? num.slice(1, -1) : num;
          return `(${numerator})/${den}`;
        })
        .replace(/([a-zA-Z0-9±√\s()]+)\s*\/\s*(\d+[a-zA-Z]?|[a-zA-Z]+\d*)/g, (match, num, den, offset, string) => {
          // Проверяем контекст
          const before = offset > 0 ? string.substring(Math.max(0, offset - 10), offset) : '';
          const after = offset + match.length < string.length ? string.substring(offset + match.length, Math.min(string.length, offset + match.length + 10)) : '';
          
          if ((/[=:\s]|^/.test(before.slice(-1)) || before.trim() === '') && 
              (/[\s=,\n]|$/.test(after.charAt(0)) || after.trim() === '')) {
            if (!num.trim().startsWith('(') && /[+\-±√]/.test(num)) {
              return `(${num.trim()})/${den}`;
            }
          }
          return match;
        });
    };

    const processedContent = material.content ? processContentForMath(material.content) : '';
    return (
      <div className="prose prose-lg max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({node, ...props}) => (
              <h1 className="text-3xl font-bold text-gray-900 mt-8 mb-4 pb-3 border-b-2 border-blue-200" {...props} />
            ),
            h2: ({node, ...props}) => (
              <h2 className="text-2xl font-semibold text-gray-900 mt-8 mb-4 flex items-center gap-2">
                <div className="w-1 h-8 bg-gradient-to-b from-blue-500 to-purple-600 rounded-full" />
                <span {...props} />
              </h2>
            ),
            h3: ({node, ...props}) => (
              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3 flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span {...props} />
              </h3>
            ),
            p: ({node, children, ...props}: any) => {
              // Для параграфов применяем форматирование только если есть формулы
              const text = typeof children === 'string' ? children : 
                          Array.isArray(children) ? children.map(c => typeof c === 'string' ? c : '').join('') : '';
              
              // Проверяем, есть ли в тексте дроби или формулы
              const hasFormulas = /\/\s*\d+|\d+\s*\/|\([^)]+\)\s*\/|√|²|³/.test(text);
              
              if (hasFormulas) {
                const formatted = formatMathText(text);
                return (
                  <p className="text-gray-900 mb-4 leading-relaxed text-base" {...props}>
                    {formatted}
                  </p>
                );
              }
              
              // Если формул нет, просто возвращаем обычный текст
              return (
                <p className="text-gray-900 mb-4 leading-relaxed text-base" {...props}>
                  {children}
                </p>
              );
            },
            strong: ({node, children, ...props}: any) => {
              // Применяем форматирование к жирному тексту, если там есть формулы
              const text = typeof children === 'string' ? children : 
                          Array.isArray(children) ? children.map(c => typeof c === 'string' ? c : '').join('') : '';
              const hasFormulas = /\/\s*\d+|\d+\s*\/|\([^)]+\)\s*\/|√|²|³/.test(text);
              
              if (hasFormulas) {
                const formatted = formatMathText(text);
                return (
                  <strong className="text-gray-900 font-semibold" {...props}>
                    {formatted}
                  </strong>
                );
              }
              
              return (
                <strong className="text-gray-900 font-semibold" {...props}>
                  {children}
                </strong>
              );
            },
            ul: ({node, ...props}) => (
              <ul className="list-none space-y-2 mb-4" {...props} />
            ),
            ol: ({node, ...props}) => (
              <ol className="list-decimal list-inside space-y-2 mb-4 ml-4" {...props} />
            ),
            li: ({node, children, ...props}: any) => {
              // Правильно извлекаем текст из children, обрабатывая React элементы
              const extractText = (children: any): string => {
                if (typeof children === 'string') return children;
                if (Array.isArray(children)) {
                  return children.map(child => {
                    if (typeof child === 'string') return child;
                    if (typeof child === 'object' && child !== null) {
                      // Если это React элемент, пытаемся извлечь текст из props.children
                      if (child.props && child.props.children) {
                        return extractText(child.props.children);
                      }
                      return '';
                    }
                    return String(child);
                  }).join('');
                }
                if (typeof children === 'object' && children !== null) {
                  if (children.props && children.props.children) {
                    return extractText(children.props.children);
                  }
                }
                return String(children);
              };
              
              const text = extractText(children);
              
              // Проверяем специальные маркеры
              if (text.startsWith('✓') || text.includes('✓')) {
                return (
                  <li className="flex items-start gap-3 p-3 bg-green-50 rounded-lg mb-2 border-l-4 border-green-500">
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 flex-1">{text.replace(/✓\s*/, '')}</span>
                  </li>
                );
              }
              if (text.startsWith('💡') || text.includes('💡')) {
                return (
                  <li className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg mb-2 border-l-4 border-yellow-500">
                    <Lightbulb className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 flex-1">{text.replace(/💡\s*/, '')}</span>
                  </li>
                );
              }
              if (text.startsWith('⚠') || text.includes('⚠') || text.startsWith('Важно')) {
                return (
                  <li className="flex items-start gap-3 p-3 bg-orange-50 rounded-lg mb-2 border-l-4 border-orange-500">
                    <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 flex-1 font-semibold">{text.replace(/⚠\s*/, '')}</span>
                  </li>
                );
              }
              return (
                <li className="flex items-start gap-3 p-2 text-gray-700" {...props}>
                  <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-2" />
                  <span className="flex-1">{children}</span>
                </li>
              );
            },
            code: ({node, inline, children, ...props}: any) => {
              if (inline) {
                const text = typeof children === 'string' ? children : 
                            Array.isArray(children) ? children.map(c => typeof c === 'string' ? c : '').join('') : '';
                const formatted = formatMathText(text);
                return (
                  <code className="px-2 py-1 bg-blue-50 text-blue-700 rounded font-mono text-sm border border-blue-200" {...props}>
                    {formatted}
                  </code>
                );
              }
              const text = typeof children === 'string' ? children : 
                          Array.isArray(children) ? children.map(c => typeof c === 'string' ? c : '').join('') : '';
              const formatted = formatMathText(text);
              return (
                <code className="block p-4 bg-white text-gray-900 rounded-lg font-mono text-sm overflow-x-auto mb-4 border border-gray-200" {...props}>
                  {formatted}
                </code>
              );
            },
            pre: ({node, children, ...props}: any) => {
              return (
                <pre className="mb-4" {...props}>
                  {children}
                </pre>
              );
            },
            blockquote: ({node, ...props}) => (
              <blockquote className="border-l-4 border-purple-500 pl-4 py-2 bg-purple-50 rounded-r-lg my-4 italic text-gray-700" {...props} />
            ),
            table: ({node, ...props}) => (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full border-collapse border border-gray-300 rounded-lg" {...props} />
              </div>
            ),
            th: ({node, ...props}) => (
              <th className="border border-gray-300 px-4 py-2 bg-blue-50 text-left font-semibold text-gray-900" {...props} />
            ),
            td: ({node, ...props}) => (
              <td className="border border-gray-300 px-4 py-2 text-gray-700" {...props} />
            ),
          }}
        >
          {processedContent}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className={`bg-gradient-to-r ${getTypeColor()} rounded-2xl p-8 text-white`}>
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-white/90 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Вернуться к библиотеке
        </button>

        <div className="flex items-start gap-6">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm flex-shrink-0">
            {getTypeIcon()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm">
                {material.subject}
              </span>
              <span className="px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm">
                {material.topic}
              </span>
            </div>
            <h1 className="text-white text-2xl mb-3">{material.title}</h1>
            <p className="text-white/90 mb-4">{material.description}</p>
            
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5" />
                <span>{material.duration}</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="w-5 h-5 fill-current" />
                <span>{material.rating} рейтинг</span>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <button 
              onClick={handleShare}
              className="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-colors"
              title="Поделиться материалом"
            >
              <Share2 className="w-5 h-5" />
            </button>
            {material.type === 'pdf' && (
              <button 
                onClick={handleDownloadPDF}
                className="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-colors"
                title="Скачать PDF"
              >
                <Download className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
        <div className="xl:col-span-2 space-y-6">
          {/* Content */}
          <div 
            ref={contentRef}
            className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 max-h-[600px] overflow-y-auto"
          >
            {renderContent()}
          </div>

          {!isStudied && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-3">
              <div className="flex-1 min-w-[200px]">
                {noScrollNeeded ? (
                  <p className="text-sm text-slate-700">
                    Текст короткий, прокрутки нет. Автозасчёт через{' '}
                    <span className="font-semibold tabular-nums">{dwellRemaining}</span>
                    {' '}с или нажмите кнопку.
                  </p>
                ) : (
                  <div className="space-y-1">
                    <p className="text-sm text-slate-700">
                      Прогресс чтения:{' '}
                      <span className="font-semibold tabular-nums">{Math.round(scrollProgress)}</span>%
                    </p>
                    <div className="h-2 rounded-full bg-slate-200 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-600 transition-all duration-300"
                        style={{ width: `${Math.min(100, scrollProgress)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
              <button
                type="button"
                disabled={isMarking}
                onClick={() => void handleMarkAsStudied(1)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:pointer-events-none shrink-0"
              >
                <CheckCircle className="w-4 h-4" />
                {isMarking ? 'Сохраняем…' : 'Засчитать как изученное'}
              </button>
            </div>
          )}

          {/* Practice Section (показываем в конце материала) */}
          {(scrollProgress >= SCROLL_COMPLETE_PCT || isStudied) && (
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-gray-900 mb-2">Готов проверить знания?</h3>
                  <p className="text-gray-600">
                    {isStudied
                      ? 'Отлично! Теперь закрепи материал, решив адаптивные задания по этой теме'
                      : 'Материал дочитан. Можно переходить к практике.'}
                  </p>
                </div>
                <button 
                  onClick={() => {
                    // Переходим к адаптивным заданиям с выбранной темой
                    const event = new CustomEvent('navigateToTasks', { detail: { topic: material.topic } });
                    window.dispatchEvent(event);
                  }}
                  className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors flex items-center gap-2"
                >
                  <Target className="w-5 h-5" />
                  Практиковаться
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Related Materials */}
        <aside className="xl:col-span-1 bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-gray-900 mb-4">Связанные материалы</h3>
          <div className="space-y-3">
            {(material.related_ids && material.related_ids.length > 0
              ? material.related_ids
                  .map((id) => allMaterials.find((m) => m.id === id))
                  .filter((m): m is Material => Boolean(m))
              : []
            ).map((related) => (
              <button
                key={related.id}
                type="button"
                onClick={() => onSelectRelated?.(related)}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50/50 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-3 mb-2">
                  <BookOpen className="w-5 h-5 text-blue-600 shrink-0" />
                  <span className="text-sm font-medium text-gray-900">{related.title}</span>
                </div>
                <p className="text-xs text-gray-500">{related.description || related.topic}</p>
              </button>
            ))}
            {(!material.related_ids || material.related_ids.length === 0) && (
              <p className="text-sm text-gray-500">Нет связанных материалов</p>
            )}
          </div>
        </aside>
      </div>
    </motion.div>
  );
}
