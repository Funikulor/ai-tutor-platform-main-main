import { ArrowLeft, BookOpen, Video, FileText, Clock, Star, Download, Share2 } from 'lucide-react';
import { motion } from 'motion/react';
import type { Material } from './LibraryTab';

interface MaterialViewerProps {
  material: Material;
  onBack: () => void;
}

export function MaterialViewer({ material, onBack }: MaterialViewerProps) {
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

  const renderContent = () => {
    if (material.type === 'video') {
      return (
        <div className="space-y-6">
          <div className="bg-gray-900 rounded-xl aspect-video flex items-center justify-center">
            <div className="text-center text-white">
              <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-gray-400">Видео будет загружено здесь</p>
              <p className="text-sm text-gray-500 mt-2">{material.videoUrl}</p>
            </div>
          </div>
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
              <button className="px-6 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-colors flex items-center gap-2 mx-auto">
                <Download className="w-5 h-5" />
                Скачать PDF
              </button>
            </div>
          </div>
        </div>
      );
    }

    // Article content with markdown-style rendering
    return (
      <div className="prose prose-lg max-w-none">
        {material.content?.split('\n').map((line, index) => {
          // Headers
          if (line.startsWith('# ')) {
            return <h1 key={index} className="text-gray-900 mt-8 mb-4">{line.substring(2)}</h1>;
          }
          if (line.startsWith('## ')) {
            return <h2 key={index} className="text-gray-900 mt-6 mb-3">{line.substring(3)}</h2>;
          }
          if (line.startsWith('### ')) {
            return <h3 key={index} className="text-gray-800 mt-4 mb-2">{line.substring(4)}</h3>;
          }
          
          // Bold text
          if (line.includes('**')) {
            const parts = line.split('**');
            return (
              <p key={index} className="text-gray-700 mb-3">
                {parts.map((part, i) => 
                  i % 2 === 1 ? <strong key={i} className="text-gray-900">{part}</strong> : part
                )}
              </p>
            );
          }

          // List items
          if (line.startsWith('- ')) {
            return <li key={index} className="text-gray-700 ml-4">{line.substring(2)}</li>;
          }
          if (line.match(/^\d+\./)) {
            return <li key={index} className="text-gray-700 ml-4">{line.substring(line.indexOf('.') + 2)}</li>;
          }

          // Special markers
          if (line.startsWith('✓')) {
            return (
              <div key={index} className="flex items-start gap-2 p-3 bg-green-50 rounded-lg mb-2">
                <span className="text-green-600">✓</span>
                <span className="text-gray-700">{line.substring(2)}</span>
              </div>
            );
          }

          // Code blocks or special formatting
          if (line.startsWith('{') || line.startsWith('}')) {
            return <div key={index} className="font-mono text-sm bg-gray-100 p-2 rounded">{line}</div>;
          }

          // Empty lines
          if (line.trim() === '') {
            return <div key={index} className="h-2" />;
          }

          // Regular paragraphs
          return <p key={index} className="text-gray-700 mb-3 leading-relaxed">{line}</p>;
        })}
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
            <h1 className="text-white text-3xl mb-3">{material.title}</h1>
            <p className="text-white/90 text-lg mb-4">{material.description}</p>
            
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
            <button className="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-colors">
              <Share2 className="w-5 h-5" />
            </button>
            {material.type === 'pdf' && (
              <button className="w-10 h-10 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-colors">
                <Download className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        {renderContent()}
      </div>

      {/* Related Materials */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-gray-900 mb-4">Связанные материалы</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 border border-gray-200 rounded-lg hover:border-blue-400 transition-colors cursor-pointer">
              <div className="flex items-center gap-3 mb-2">
                <BookOpen className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-gray-900">Связанная тема {i}</span>
              </div>
              <p className="text-xs text-gray-500">Дополнительный материал для углубленного изучения</p>
            </div>
          ))}
        </div>
      </div>

      {/* Practice Section */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-gray-900 mb-2">Готов проверить знания?</h3>
            <p className="text-gray-600">Пройди тест по этой теме и закрепи материал</p>
          </div>
          <button className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors">
            Начать тест
          </button>
        </div>
      </div>
    </motion.div>
  );
}
