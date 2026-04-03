import { useState, useEffect } from 'react';
import { User, Mail, Phone, GraduationCap, Calendar, Shield, Edit2, Save, X, Wand2, Loader2 } from 'lucide-react';
import api from '../services/api';
import { avatarInitial, getAvatarUrl, randomAvatarSeed } from '../utils/avatar';
import { toast } from 'sonner';

interface UserProfileData {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  class_id?: string;
  phone?: string;
  avatar_seed?: string | null;
  is_active?: boolean;
  created_at?: string;
  analytics?: any;
}

interface UserProfileProps {
  userId?: string;
  onClose?: () => void;
  onProfileUpdated?: () => void;
}

export function UserProfile({ userId, onClose, onProfileUpdated }: UserProfileProps) {
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<UserProfileData | null>(null);
  const [avatarImageFailed, setAvatarImageFailed] = useState(false);
  const [avatarSaving, setAvatarSaving] = useState(false);

  const activeAvatarSeed = editing ? editData?.avatar_seed : profile?.avatar_seed;

  useEffect(() => {
    setAvatarImageFailed(false);
  }, [activeAvatarSeed, editing]);

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const loadProfile = async (options?: { showSpinner?: boolean }) => {
    const showSpinner = options?.showSpinner !== false;
    if (showSpinner) setLoading(true);
    try {
      const targetUserId = userId || localStorage.getItem('user_id');
      if (!targetUserId) {
        return;
      }

      const token = localStorage.getItem('token');
      const response = await api.get(`/auth/profile`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setProfile(response.data);
      setEditData(response.data);
    } catch (error: any) {
      console.error('Error loading profile:', error);
      const userData = {
        user_id: localStorage.getItem('user_id') || '',
        email: localStorage.getItem('email') || '',
        full_name: localStorage.getItem('full_name') || '',
        role: localStorage.getItem('role') || 'student',
      };
      setProfile(userData as UserProfileData);
      setEditData(userData as UserProfileData);
    } finally {
      if (showSpinner) setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!editData) return;
    
    try {
      const token = localStorage.getItem('token');
      await api.put('/auth/profile', {
        full_name: editData.full_name,
        phone: editData.phone ?? '',
        avatar_seed: editData.avatar_seed ?? null,
      }, { headers: { Authorization: `Bearer ${token}` } });
      setProfile(editData);
      setEditing(false);
      if (editData.full_name) {
        localStorage.setItem('full_name', editData.full_name);
      }
      onProfileUpdated?.();
      toast.success('Профиль сохранён');
    } catch (error: any) {
      console.error('Error saving profile:', error);
      const msg = error?.response?.data?.detail;
      toast.error(typeof msg === 'string' ? msg : 'Не удалось сохранить профиль');
    }
  };

  /** Новый seed сразу уходит на сервер — без отдельного «Сохранить» только для аватара */
  const handleRegenerateAvatar = async () => {
    if (!profile) return;
    const newSeed = randomAvatarSeed();
    setAvatarImageFailed(false);
    setAvatarSaving(true);
    setEditData((e) => (e ? { ...e, avatar_seed: newSeed } : e));
    setProfile((p) => (p ? { ...p, avatar_seed: newSeed } : p));
    try {
      const { data } = await api.put<UserProfileData>('/auth/profile', { avatar_seed: newSeed });
      setProfile(data);
      setEditData(data);
      if (data.full_name) {
        localStorage.setItem('full_name', data.full_name);
      }
      onProfileUpdated?.();
      toast.success('Аватар обновлён');
    } catch (error: any) {
      console.error('Error updating avatar:', error);
      const msg = error?.response?.data?.detail;
      toast.error(typeof msg === 'string' ? msg : 'Не удалось сохранить аватар');
      await loadProfile({ showSpinner: false });
    } finally {
      setAvatarSaving(false);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="w-5 h-5" />;
      case 'teacher':
        return <GraduationCap className="w-5 h-5" />;
      case 'student':
        return <User className="w-5 h-5" />;
      default:
        return <User className="w-5 h-5" />;
    }
  };

  const getRoleName = (role: string) => {
    const names: Record<string, string> = {
      admin: 'Администратор',
      teacher: 'Учитель',
      student: 'Ученик',
      parent: 'Родитель',
    };
    return names[role] || role;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="p-8 text-center text-gray-500">
        Профиль не найден
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex min-w-0 flex-1 items-center gap-4">
          <div className="flex shrink-0 items-center gap-3">
            {(() => {
              const url = getAvatarUrl(activeAvatarSeed ?? undefined, 192);
              const showImg = Boolean(url) && !avatarImageFailed;
              return (
                <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-full border-2 border-gray-200 bg-slate-200">
                  {showImg ? (
                    <img
                      src={url!}
                      alt=""
                      width={64}
                      height={64}
                      className="absolute inset-0 h-full w-full object-cover object-center"
                      onError={() => setAvatarImageFailed(true)}
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center">
                      <span className="select-none text-2xl font-bold leading-none text-slate-800">
                        {avatarInitial(profile.full_name)}
                      </span>
                    </div>
                  )}
                </div>
              );
            })()}
            <div className="flex flex-col gap-1">
              <button
                type="button"
                onClick={() => void handleRegenerateAvatar()}
                disabled={avatarSaving}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-sm font-medium text-violet-900 shadow-sm transition hover:bg-violet-100 disabled:cursor-not-allowed disabled:opacity-60"
                title="Сгенерировать новый аватар и сохранить"
              >
                {avatarSaving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Wand2 className="h-4 w-4" />
                )}
                {avatarSaving ? 'Сохранение…' : 'Другой аватар'}
              </button>
              <p className="max-w-[200px] text-xs text-gray-500">
                Случайный образ сразу сохраняется в профиль
              </p>
            </div>
          </div>
          <div className="min-w-0">
            <h2 className="text-2xl font-bold text-gray-900">
              {editing ? (
                <input
                  type="text"
                  value={editData?.full_name || ''}
                  onChange={(e) => setEditData({ ...editData!, full_name: e.target.value })}
                  className="border border-gray-300 rounded px-2 py-1"
                />
              ) : (
                profile.full_name
              )}
            </h2>
            <div className="flex items-center gap-2 mt-1">
              {getRoleIcon(profile.role)}
              <span className="text-gray-600">{getRoleName(profile.role)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                title="Сохранить"
              >
                <Save className="w-5 h-5" />
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setEditData(profile);
                }}
                className="p-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                title="Отмена"
              >
                <X className="w-5 h-5" />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setEditing(true)}
                className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                title="Редактировать"
              >
                <Edit2 className="w-5 h-5" />
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="p-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  title="Закрыть"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Profile Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <Mail className="w-5 h-5 text-gray-500" />
          <div>
            <p className="text-sm text-gray-500">Email</p>
            <p className="font-medium text-gray-900">
              {editing ? (
                <input
                  type="email"
                  value={editData?.email || ''}
                  onChange={(e) => setEditData({ ...editData!, email: e.target.value })}
                  className="border border-gray-300 rounded px-2 py-1 w-full mt-1"
                />
              ) : (
                profile.email
              )}
            </p>
          </div>
        </div>

        {profile.phone && (
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
            <Phone className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-500">Телефон</p>
              <p className="font-medium text-gray-900">
                {editing ? (
                  <input
                    type="tel"
                    value={editData?.phone || ''}
                    onChange={(e) => setEditData({ ...editData!, phone: e.target.value })}
                    className="border border-gray-300 rounded px-2 py-1 w-full mt-1"
                  />
                ) : (
                  profile.phone
                )}
              </p>
            </div>
          </div>
        )}

        {profile.class_id && (
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
            <GraduationCap className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-500">Класс</p>
              <p className="font-medium text-gray-900">
                {editing ? (
                  <input
                    type="text"
                    value={editData?.class_id || ''}
                    onChange={(e) => setEditData({ ...editData!, class_id: e.target.value })}
                    className="border border-gray-300 rounded px-2 py-1 w-full mt-1"
                  />
                ) : (
                  profile.class_id
                )}
              </p>
            </div>
          </div>
        )}

        {profile.created_at && (
          <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
            <Calendar className="w-5 h-5 text-gray-500" />
            <div>
              <p className="text-sm text-gray-500">Дата регистрации</p>
              <p className="font-medium text-gray-900">
                {new Date(profile.created_at).toLocaleDateString('ru-RU')}
              </p>
            </div>
          </div>
        )}

        <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
          <Shield className="w-5 h-5 text-gray-500" />
          <div>
            <p className="text-sm text-gray-500">ID пользователя</p>
            <p className="font-medium text-gray-900 font-mono text-sm">{profile.user_id}</p>
          </div>
        </div>
      </div>

      {/* Analytics (если есть) */}
      {profile.analytics && (
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Аналитика</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-600">Взаимодействий</p>
              <p className="text-2xl font-bold text-blue-900">
                {profile.analytics.total_interactions || 0}
              </p>
            </div>
            {profile.analytics.academic_traits && (
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">Точность тестов</p>
                <p className="text-2xl font-bold text-green-900">
                  {profile.analytics.academic_traits.test_accuracy || '0%'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}



















