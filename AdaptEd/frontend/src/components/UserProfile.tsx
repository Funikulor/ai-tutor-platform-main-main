import { useState, useEffect } from 'react';
import { User, Mail, Phone, GraduationCap, Calendar, Shield, Edit2, Save, X, ImagePlus } from 'lucide-react';
import api from '../services/api';
import { getAvatarUrl, randomAvatarSeed } from '../utils/avatar';

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

  useEffect(() => {
    loadProfile();
  }, [userId]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const targetUserId = userId || localStorage.getItem('user_id');
      if (!targetUserId) {
        setLoading(false);
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
      // Fallback: используем данные из localStorage
      const userData = {
        user_id: localStorage.getItem('user_id') || '',
        email: localStorage.getItem('email') || '',
        full_name: localStorage.getItem('full_name') || '',
        role: localStorage.getItem('role') || 'student',
      };
      setProfile(userData as UserProfileData);
      setEditData(userData as UserProfileData);
    } finally {
      setLoading(false);
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
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  const handleChangeAvatar = () => {
    if (!editData) return;
    setEditData({ ...editData, avatar_seed: randomAvatarSeed() });
  };

  const handleChangeAvatarQuick = async () => {
    const newSeed = randomAvatarSeed();
    try {
      const token = localStorage.getItem('token');
      await api.put('/auth/profile', { avatar_seed: newSeed }, { headers: { Authorization: `Bearer ${token}` } });
      setProfile((p) => (p ? { ...p, avatar_seed: newSeed } : p));
      setEditData((e) => (e ? { ...e, avatar_seed: newSeed } : e));
      onProfileUpdated?.();
    } catch (error) {
      console.error('Error updating avatar:', error);
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
        <div className="flex items-center gap-4">
          <div className="relative">
            {(editing ? getAvatarUrl(editData?.avatar_seed ?? undefined) : getAvatarUrl(profile.avatar_seed)) ? (
              <img
                src={editing ? getAvatarUrl(editData?.avatar_seed ?? undefined)! : getAvatarUrl(profile.avatar_seed)!}
                alt=""
                className="w-16 h-16 rounded-full object-cover border-2 border-gray-200"
              />
            ) : (
              <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                {profile.full_name.charAt(0).toUpperCase()}
              </div>
            )}
            {editing ? (
              <button
                type="button"
                onClick={handleChangeAvatar}
                className="absolute -bottom-1 -right-1 p-1.5 bg-blue-500 text-white rounded-full shadow hover:bg-blue-600 transition-colors"
                title="Сменить аватар"
              >
                <ImagePlus className="w-4 h-4" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleChangeAvatarQuick}
                className="absolute -bottom-1 -right-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-xs shadow transition-colors"
                title="Сменить аватар"
              >
                <ImagePlus className="w-3.5 h-3.5 inline mr-0.5" />
                Аватар
              </button>
            )}
          </div>
          <div>
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



















