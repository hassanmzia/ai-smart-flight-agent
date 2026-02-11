import { useState, useEffect, useRef } from 'react';
import { useAuth, useRequireAuth } from '@/hooks/useAuth';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import { toast } from 'react-hot-toast';
import profileService, { UpdateUserData, UpdateProfileData, ChangePasswordData } from '@/services/profileService';
import { UserCircleIcon, CameraIcon } from '@heroicons/react/24/outline';

type TabType = 'account' | 'profile' | 'security' | 'preferences';

const ProfilePage = () => {
  useRequireAuth();
  const { user, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('account');
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Account form state
  const [accountData, setAccountData] = useState<UpdateUserData>({
    first_name: '',
    last_name: '',
    phone_number: '',
  });

  // Profile form state
  const [profileData, setProfileData] = useState<UpdateProfileData>({
    date_of_birth: '',
    nationality: '',
    bio: '',
    preferred_currency: 'USD',
    preferred_language: 'en',
  });

  // Password form state
  const [passwordData, setPasswordData] = useState<ChangePasswordData>({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });

  // Avatar upload
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);

  useEffect(() => {
    if (user) {
      setAccountData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        phone_number: user.phone_number || '',
      });

      setAvatarPreview(user.profile?.avatar || null);
    }
  }, [user]);

  const handleAccountUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await profileService.updateUser(accountData);
      await refreshUser();
      toast.success('Account information updated successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update account information');
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await profileService.updateProfile(profileData);
      await refreshUser();
      toast.success('Profile updated successfully!');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.new_password !== passwordData.new_password_confirm) {
      toast.error('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await profileService.changePassword(passwordData);
      setPasswordData({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
      });
      toast.success('Password changed successfully!');
    } catch (error: any) {
      const errorMsg = error.response?.data?.old_password?.[0] ||
                      error.response?.data?.new_password?.[0] ||
                      error.response?.data?.message ||
                      'Failed to change password';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Image size must be less than 5MB');
        return;
      }

      // Check file type
      if (!file.type.startsWith('image/')) {
        toast.error('Please select an image file');
        return;
      }

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result as string);
      };
      reader.readAsDataURL(file);

      // Upload avatar
      uploadAvatar(file);
    }
  };

  const uploadAvatar = async (file: File) => {
    setUploadingAvatar(true);

    try {
      const result = await profileService.uploadAvatar(file);
      await profileService.updateProfile({ avatar: result.avatar_url });
      await refreshUser();
      toast.success('Profile picture updated successfully!');
    } catch (error: any) {
      toast.error('Failed to upload profile picture');
      setAvatarPreview(user?.profile?.avatar || null);
    } finally {
      setUploadingAvatar(false);
    }
  };

  const tabs = [
    { id: 'account' as TabType, label: 'Account', icon: '👤' },
    { id: 'profile' as TabType, label: 'Profile', icon: '📝' },
    { id: 'security' as TabType, label: 'Security', icon: '🔒' },
    { id: 'preferences' as TabType, label: 'Preferences', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            My Profile
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Profile Picture */}
        <Card className="mb-6">
          <CardContent className="text-center py-8">
            <div className="relative inline-block">
              <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 flex items-center justify-center mx-auto mb-4 border-4 border-white dark:border-gray-800 shadow-lg">
                {avatarPreview ? (
                  <img
                    src={avatarPreview}
                    alt="Profile"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <UserCircleIcon className="w-20 h-20 text-gray-400" />
                )}
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingAvatar}
                className="absolute bottom-4 right-0 bg-primary-600 hover:bg-primary-700 text-white p-2 rounded-full shadow-lg transition-colors disabled:opacity-50"
                title="Change profile picture"
              >
                <CameraIcon className="w-5 h-5" />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarSelect}
                className="hidden"
              />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              {user?.full_name || 'User'}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">{user?.email}</p>
            {user?.is_verified && (
              <span className="inline-flex items-center px-3 py-1 mt-2 rounded-full text-sm font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                ✓ Verified
              </span>
            )}
          </CardContent>
        </Card>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Account Tab */}
        {activeTab === 'account' && (
          <Card>
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAccountUpdate} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="First Name"
                    value={accountData.first_name}
                    onChange={(e) =>
                      setAccountData({ ...accountData, first_name: e.target.value })
                    }
                    placeholder="Enter your first name"
                    required
                  />
                  <Input
                    label="Last Name"
                    value={accountData.last_name}
                    onChange={(e) =>
                      setAccountData({ ...accountData, last_name: e.target.value })
                    }
                    placeholder="Enter your last name"
                    required
                  />
                </div>

                <Input
                  label="Email Address"
                  value={user?.email || ''}
                  disabled
                  helperText="Email cannot be changed. Contact support if needed."
                />

                <Input
                  label="Phone Number"
                  value={accountData.phone_number}
                  onChange={(e) =>
                    setAccountData({ ...accountData, phone_number: e.target.value })
                  }
                  placeholder="+1234567890"
                />

                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Member since {new Date(user?.date_joined || '').toLocaleDateString()}
                  </p>
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <Card>
            <CardHeader>
              <CardTitle>Profile Details</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileUpdate} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Bio
                  </label>
                  <textarea
                    value={profileData.bio}
                    onChange={(e) =>
                      setProfileData({ ...profileData, bio: e.target.value })
                    }
                    rows={4}
                    maxLength={500}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Tell us about yourself..."
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {profileData.bio?.length || 0}/500 characters
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="Date of Birth"
                    type="date"
                    value={profileData.date_of_birth}
                    onChange={(e) =>
                      setProfileData({ ...profileData, date_of_birth: e.target.value })
                    }
                  />
                  <Input
                    label="Nationality"
                    value={profileData.nationality}
                    onChange={(e) =>
                      setProfileData({ ...profileData, nationality: e.target.value })
                    }
                    placeholder="e.g., American, British"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Preferred Currency
                    </label>
                    <select
                      value={profileData.preferred_currency}
                      onChange={(e) =>
                        setProfileData({ ...profileData, preferred_currency: e.target.value })
                      }
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="USD">USD - US Dollar</option>
                      <option value="EUR">EUR - Euro</option>
                      <option value="GBP">GBP - British Pound</option>
                      <option value="CAD">CAD - Canadian Dollar</option>
                      <option value="AUD">AUD - Australian Dollar</option>
                      <option value="JPY">JPY - Japanese Yen</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Preferred Language
                    </label>
                    <select
                      value={profileData.preferred_language}
                      onChange={(e) =>
                        setProfileData({ ...profileData, preferred_language: e.target.value })
                      }
                      className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                      <option value="it">Italian</option>
                      <option value="ja">Japanese</option>
                    </select>
                  </div>
                </div>

                {/* Travel Stats */}
                {user?.profile && (
                  <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                      Travel Statistics
                    </h3>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                          {user.profile.total_trips}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Total Trips
                        </div>
                      </div>
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                          {user.profile.total_flights}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Flights
                        </div>
                      </div>
                      <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                        <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                          {user.profile.total_hotel_nights}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Hotel Nights
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Saving...' : 'Save Profile'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handlePasswordChange} className="space-y-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
                    Password Requirements:
                  </h4>
                  <ul className="text-sm text-blue-800 dark:text-blue-400 space-y-1">
                    <li>• At least 8 characters long</li>
                    <li>• Mix of letters, numbers, and symbols recommended</li>
                    <li>• Avoid common words and personal information</li>
                  </ul>
                </div>

                <Input
                  label="Current Password"
                  type="password"
                  value={passwordData.old_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, old_password: e.target.value })
                  }
                  placeholder="Enter your current password"
                  required
                />

                <Input
                  label="New Password"
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) =>
                    setPasswordData({ ...passwordData, new_password: e.target.value })
                  }
                  placeholder="Enter your new password"
                  required
                />

                <Input
                  label="Confirm New Password"
                  type="password"
                  value={passwordData.new_password_confirm}
                  onChange={(e) =>
                    setPasswordData({
                      ...passwordData,
                      new_password_confirm: e.target.value,
                    })
                  }
                  placeholder="Confirm your new password"
                  required
                />

                <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Button type="submit" disabled={loading}>
                    {loading ? 'Changing Password...' : 'Change Password'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Preferences Tab */}
        {activeTab === 'preferences' && (
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      Email Notifications
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Receive booking confirmations and travel updates via email
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={user?.profile?.email_notifications ?? true}
                      onChange={(e) =>
                        profileService.updateProfile({
                          email_notifications: e.target.checked,
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      Push Notifications
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Get instant alerts for price drops and trip updates
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={user?.profile?.push_notifications ?? true}
                      onChange={(e) =>
                        profileService.updateProfile({
                          push_notifications: e.target.checked,
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      SMS Notifications
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Receive important updates via text message
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={user?.profile?.sms_notifications ?? false}
                      onChange={(e) =>
                        profileService.updateProfile({
                          sms_notifications: e.target.checked,
                        })
                      }
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
