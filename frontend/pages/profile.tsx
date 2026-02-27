// pages/profile.tsx - User Profile Page
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';

function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '—';
    try {
        return new Date(dateStr).toLocaleDateString('en-IN', {
            day: 'numeric', month: 'short', year: 'numeric'
        });
    } catch { return '—'; }
}

export default function ProfilePage() {
    const router = useRouter();
    const { user, logout, updateProfile } = useAuth();
    const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'settings'>('profile');

    // Profile form state
    const [profileForm, setProfileForm] = useState({
        full_name: '',
        phone: '',
        company: '',
        designation: '',
        bio: '',
    });
    const [profileLoading, setProfileLoading] = useState(false);
    const [profileSuccess, setProfileSuccess] = useState(false);
    const [profileError, setProfileError] = useState<string | null>(null);

    // Password form state
    const [passwordForm, setPasswordForm] = useState({
        current_password: '',
        new_password: '',
        confirm_new_password: '',
    });
    const [passwordLoading, setPasswordLoading] = useState(false);
    const [passwordSuccess, setPasswordSuccess] = useState(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);

    // Delete account
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [deleteLoading, setDeleteLoading] = useState(false);

    useEffect(() => {
        if (user) {
            setProfileForm({
                full_name: (user as any).full_name || '',
                phone: (user as any).phone || '',
                company: (user as any).company || '',
                designation: (user as any).designation || '',
                bio: (user as any).bio || '',
            });
        }
    }, [user]);

    // Redirect to home if not logged in
    useEffect(() => {
        if (!user) {
            router.push('/');
        }
    }, [user]);

    if (!user) {
        return (
            <Layout title="Profile - NexIPO">
                <div className="max-w-4xl mx-auto px-4 py-12 text-center">
                    <p className="text-gray-600">Please sign in to view your profile.</p>
                </div>
            </Layout>
        );
    }

    const handleProfileSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setProfileLoading(true);
        setProfileError(null);
        setProfileSuccess(false);

        try {
            await updateProfile(profileForm);
            setProfileSuccess(true);
            setTimeout(() => setProfileSuccess(false), 3000);
        } catch (err: any) {
            setProfileError(err.message);
        } finally {
            setProfileLoading(false);
        }
    };

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setPasswordLoading(true);
        setPasswordError(null);
        setPasswordSuccess(false);

        if (passwordForm.new_password !== passwordForm.confirm_new_password) {
            setPasswordError('New passwords do not match');
            setPasswordLoading(false);
            return;
        }

        try {
            await apiService.changePassword(passwordForm);
            setPasswordSuccess(true);
            setPasswordForm({ current_password: '', new_password: '', confirm_new_password: '' });
            setTimeout(() => setPasswordSuccess(false), 3000);
        } catch (err: any) {
            setPasswordError(err.response?.data?.detail || err.message || 'Password change failed');
        } finally {
            setPasswordLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        setDeleteLoading(true);
        try {
            await apiService.deleteAccount();
            logout();
            router.push('/');
        } catch (err: any) {
            setPasswordError(err.response?.data?.detail || 'Failed to delete account');
        } finally {
            setDeleteLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        router.push('/');
    };

    const tabs = [
        {
            key: 'profile' as const, label: 'Profile', icon: (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            )
        },
        {
            key: 'security' as const, label: 'Security', icon: (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
            )
        },
        {
            key: 'settings' as const, label: 'Settings', icon: (
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            )
        },
    ];

    return (
        <Layout title="Profile - NexIPO">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

                {/* Profile Header */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 mb-6">
                    <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
                        {/* Avatar */}
                        <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-700 rounded-full flex items-center justify-center ring-4 ring-primary-100">
                            <span className="text-white font-bold text-3xl">
                                {user.username[0].toUpperCase()}
                            </span>
                        </div>

                        {/* User Info */}
                        <div className="flex-1 text-center sm:text-left">
                            <h1 className="text-2xl font-bold text-gray-900">
                                {(user as any).full_name || user.username}
                            </h1>
                            <p className="text-gray-500">@{user.username}</p>
                            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 mt-3">
                                <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                    {user.email}
                                </span>
                                <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    Joined {formatDate(user.created_at)}
                                </span>
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'}`}>
                                    {user.role === 'admin' ? '👑 Admin' : '👤 User'}
                                </span>
                            </div>
                        </div>

                        {/* Logout Button */}
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                            </svg>
                            Logout
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 mb-6 border-b border-gray-200 pb-0">
                    {tabs.map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.key
                                    ? 'text-primary-600 border-primary-600'
                                    : 'text-gray-500 border-transparent hover:text-gray-700 hover:border-gray-300'
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Profile Tab */}
                {activeTab === 'profile' && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
                        <h2 className="text-lg font-bold text-gray-900 mb-6">Edit Profile</h2>

                        {profileSuccess && (
                            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                                <p className="text-sm text-green-800 font-medium">✓ Profile updated successfully!</p>
                            </div>
                        )}
                        {profileError && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                <p className="text-sm text-red-800">{profileError}</p>
                            </div>
                        )}

                        <form onSubmit={handleProfileSubmit} className="space-y-5">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                                    <input
                                        type="text"
                                        value={profileForm.full_name}
                                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                                        className="input w-full"
                                        placeholder="John Doe"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                                    <input
                                        type="tel"
                                        value={profileForm.phone}
                                        onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                                        className="input w-full"
                                        placeholder="+91 98765 43210"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
                                    <input
                                        type="text"
                                        value={profileForm.company}
                                        onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
                                        className="input w-full"
                                        placeholder="Your company"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Designation</label>
                                    <input
                                        type="text"
                                        value={profileForm.designation}
                                        onChange={(e) => setProfileForm({ ...profileForm, designation: e.target.value })}
                                        className="input w-full"
                                        placeholder="Software Engineer"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
                                <textarea
                                    value={profileForm.bio}
                                    onChange={(e) => setProfileForm({ ...profileForm, bio: e.target.value })}
                                    className="input w-full h-24 resize-none"
                                    placeholder="Tell us about yourself..."
                                    maxLength={500}
                                />
                                <p className="text-xs text-gray-400 mt-1">{profileForm.bio.length}/500</p>
                            </div>

                            <div className="flex justify-end pt-2">
                                <button type="submit" disabled={profileLoading} className="btn-primary px-6 py-2.5">
                                    {profileLoading ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Security Tab */}
                {activeTab === 'security' && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
                        <h2 className="text-lg font-bold text-gray-900 mb-6">Change Password</h2>

                        {passwordSuccess && (
                            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                                <p className="text-sm text-green-800 font-medium">✓ Password changed successfully!</p>
                            </div>
                        )}
                        {passwordError && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                <p className="text-sm text-red-800">{passwordError}</p>
                            </div>
                        )}

                        <form onSubmit={handlePasswordSubmit} className="space-y-5 max-w-md">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                                <input
                                    type="password"
                                    value={passwordForm.current_password}
                                    onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                                    className="input w-full"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                                <input
                                    type="password"
                                    value={passwordForm.new_password}
                                    onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                                    className="input w-full"
                                    placeholder="••••••••"
                                    minLength={8}
                                    required
                                />
                                <p className="text-xs text-gray-500 mt-1">Minimum 8 characters</p>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                                <input
                                    type="password"
                                    value={passwordForm.confirm_new_password}
                                    onChange={(e) => setPasswordForm({ ...passwordForm, confirm_new_password: e.target.value })}
                                    className="input w-full"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                            <div className="pt-2">
                                <button type="submit" disabled={passwordLoading} className="btn-primary px-6 py-2.5">
                                    {passwordLoading ? 'Changing...' : 'Change Password'}
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Settings Tab */}
                {activeTab === 'settings' && (
                    <div className="space-y-6">
                        {/* Account Info */}
                        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
                            <h2 className="text-lg font-bold text-gray-900 mb-4">Account Information</h2>
                            <div className="space-y-3">
                                <div className="flex justify-between py-2 border-b border-gray-50">
                                    <span className="text-sm text-gray-500">Email</span>
                                    <span className="text-sm font-medium text-gray-900">{user.email}</span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-gray-50">
                                    <span className="text-sm text-gray-500">Username</span>
                                    <span className="text-sm font-medium text-gray-900">@{user.username}</span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-gray-50">
                                    <span className="text-sm text-gray-500">Role</span>
                                    <span className="text-sm font-medium text-gray-900 capitalize">{user.role}</span>
                                </div>
                                <div className="flex justify-between py-2 border-b border-gray-50">
                                    <span className="text-sm text-gray-500">Account Status</span>
                                    <span className={`text-sm font-medium ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                                        {user.is_active ? '● Active' : '○ Inactive'}
                                    </span>
                                </div>
                                <div className="flex justify-between py-2">
                                    <span className="text-sm text-gray-500">Member Since</span>
                                    <span className="text-sm font-medium text-gray-900">{formatDate(user.created_at)}</span>
                                </div>
                            </div>
                        </div>

                        {/* Danger Zone */}
                        <div className="bg-white rounded-2xl border border-red-200 shadow-sm p-6 sm:p-8">
                            <h2 className="text-lg font-bold text-red-600 mb-2">Danger Zone</h2>
                            <p className="text-sm text-gray-600 mb-4">
                                Once you delete your account, there is no going back. Please be certain.
                            </p>

                            {!showDeleteConfirm ? (
                                <button
                                    onClick={() => setShowDeleteConfirm(true)}
                                    className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                                >
                                    Delete Account
                                </button>
                            ) : (
                                <div className="bg-red-50 rounded-lg p-4">
                                    <p className="text-sm text-red-800 font-medium mb-3">
                                        Are you sure? This action will deactivate your account.
                                    </p>
                                    <div className="flex gap-3">
                                        <button
                                            onClick={handleDeleteAccount}
                                            disabled={deleteLoading}
                                            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors"
                                        >
                                            {deleteLoading ? 'Deleting...' : 'Yes, Delete My Account'}
                                        </button>
                                        <button
                                            onClick={() => setShowDeleteConfirm(false)}
                                            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
}
