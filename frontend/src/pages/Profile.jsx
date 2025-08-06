import React from 'react';
import { User, Settings, Shield, LogOut } from 'lucide-react';

const Profile = () => {
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
        <div className="text-center py-12">
          <User className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Account Management</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Update your profile information and manage account settings
          </p>
          <div className="flex justify-center space-x-4">
            <button className="btn-primary flex items-center">
              <Settings className="h-4 w-4 mr-2" />
              Edit Profile
            </button>
            <button className="btn-secondary flex items-center">
              <Shield className="h-4 w-4 mr-2" />
              Security Settings
            </button>
            <button className="btn-error flex items-center">
              <LogOut className="h-4 w-4 mr-2" />
              Delete Account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile; 