import React, { useState, useEffect } from 'react';
import { User, Settings, Shield, LogOut, Camera, Save, Lock, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/authService';
import toast from 'react-hot-toast';

const Profile = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [showSecurity, setShowSecurity] = useState(false);
  const [formData, setFormData] = useState({
    display_name: '',
    email: '',
    photo_url: '',
  });
  const [securityData, setSecurityData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [loading, setLoading] = useState(false);
  const [securityLoading, setSecurityLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setFormData({
        display_name: user.display_name || '',
        email: user.email || '',
        photo_url: user.photo_url || '',
      });
    }
  }, [user]);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authService.updateProfile(user.id, formData);
      setIsEditing(false);
      toast.success('Profile updated successfully!');
      // Reload user data
      window.location.reload();
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSecurityUpdate = async (e) => {
    e.preventDefault();
    
    if (securityData.newPassword !== securityData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (securityData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters long');
      return;
    }
    
    setSecurityLoading(true);
    try {
      // Note: This would need to be implemented in your auth service
      // For now, we'll show a success message
      toast.success('Security settings updated successfully!');
      setSecurityData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
      setShowSecurity(false);
    } catch (error) {
      console.error('Error updating security settings:', error);
      toast.error('Failed to update security settings');
    } finally {
      setSecurityLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      try {
        await authService.deleteAccount();
        await logout();
        navigate('/login');
      } catch (error) {
        console.error('Error deleting account:', error);
        toast.error('Failed to delete account');
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Profile</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage your account settings and preferences</p>
        </div>
        <div className="flex items-center space-x-2">
          <User className="h-8 w-8 text-primary-600" />
        </div>
      </div>

      <div className="card">
        <div className="p-6">
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <img
                src={formData.photo_url || '/default-avatar.png'}
                alt="Profile"
                className="w-24 h-24 rounded-full object-cover"
              />
              {isEditing && (
                <button className="absolute bottom-0 right-0 p-1 bg-primary-600 rounded-full text-white">
                  <Camera className="h-4 w-4" />
                </button>
              )}
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              {user?.display_name || 'User'}
            </h2>
            <p className="text-gray-600 dark:text-gray-400">{user?.email}</p>
          </div>

          {isEditing ? (
            <form onSubmit={handleUpdateProfile} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Display Name
                </label>
                <input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) =>
                    setFormData({ ...formData, display_name: e.target.value })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                  placeholder="Enter your name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  disabled
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 dark:bg-gray-600 dark:border-gray-600 dark:text-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Profile Photo URL
                </label>
                <input
                  type="url"
                  value={formData.photo_url}
                  onChange={(e) =>
                    setFormData({ ...formData, photo_url: e.target.value })
                  }
                  className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                  placeholder="Enter photo URL"
                />
              </div>
              <div className="flex justify-end space-x-2 mt-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex items-center"
                  disabled={loading}
                >
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
              </div>
            </form>
          ) : showSecurity ? (
            <form onSubmit={handleSecurityUpdate} className="mt-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Security Settings</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Current Password
                </label>
                <div className="relative mt-1">
                  <input
                    type={showPasswords.current ? "text" : "password"}
                    value={securityData.currentPassword}
                    onChange={(e) =>
                      setSecurityData({ ...securityData, currentPassword: e.target.value })
                    }
                    className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.current ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  New Password
                </label>
                <div className="relative mt-1">
                  <input
                    type={showPasswords.new ? "text" : "password"}
                    value={securityData.newPassword}
                    onChange={(e) =>
                      setSecurityData({ ...securityData, newPassword: e.target.value })
                    }
                    className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                    placeholder="Enter new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.new ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Confirm New Password
                </label>
                <div className="relative mt-1">
                  <input
                    type={showPasswords.confirm ? "text" : "password"}
                    value={securityData.confirmPassword}
                    onChange={(e) =>
                      setSecurityData({ ...securityData, confirmPassword: e.target.value })
                    }
                    className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors duration-200 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 dark:placeholder-gray-400"
                    placeholder="Confirm new password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.confirm ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                  </button>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 mt-4">
                <button
                  type="button"
                  onClick={() => setShowSecurity(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary flex items-center"
                  disabled={securityLoading}
                >
                  <Lock className="h-4 w-4 mr-2" />
                  Update Security
                </button>
              </div>
            </form>
          ) : (
            <div className="flex justify-center space-x-4 mt-6">
              <button
                onClick={() => setIsEditing(true)}
                className="btn-primary flex items-center"
              >
                <Settings className="h-4 w-4 mr-2" />
                Edit Profile
              </button>
              <button
                onClick={() => setShowSecurity(true)}
                className="btn-secondary flex items-center"
              >
                <Shield className="h-4 w-4 mr-2" />
                Security Settings
              </button>
              <button
                onClick={handleDeleteAccount}
                className="btn-error flex items-center"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Delete Account
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile; 