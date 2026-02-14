/**
 * Team Management Page
 * Invite and manage team members
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, Plus, Mail, Trash2, RefreshCw, Loader2, 
  CheckCircle, X, UserPlus, AlertCircle, MoreHorizontal,
  Shield, User, Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '../services/api';
import Layout from '../components/Layout';

interface TeamMember {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
  last_login: string | null;
}

interface Invitation {
  id: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
  expires_at: string;
  invited_by_name: string;
}

const roleDisplay: Record<string, string> = {
  viewer: 'Viewer',
  sales_rep: 'Sales Rep',
  manager: 'Manager',
  admin: 'Admin'
};

const roleDescription: Record<string, string> = {
  viewer: 'Can view quotes and customers',
  sales_rep: 'Can create and manage quotes',
  manager: 'Can manage team and view analytics',
  admin: 'Full access to everything'
};

export default function TeamManagement() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('sales_rep');
  const [isInviting, setIsInviting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadTeamData();
  }, []);

  const loadTeamData = async () => {
    setIsLoading(true);
    try {
      // Get team members - using auth endpoint
      const membersRes = await api.get('/auth/users');
      setMembers(membersRes.data || []);
      
      // Get pending invitations
      const invitesRes = await api.get('/team/invitations/');
      setInvitations(invitesRes.data || []);
    } catch (err: any) {
      setError('Failed to load team data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsInviting(true);

    try {
      await api.post('/team/invitations/', {
        email: inviteEmail,
        role: inviteRole
      });
      setSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteEmail('');
      setInviteRole('sales_rep');
      setShowInviteForm(false);
      loadTeamData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setIsInviting(false);
    }
  };

  const handleCancelInvite = async (inviteId: string) => {
    if (!confirm('Are you sure you want to cancel this invitation?')) return;
    
    try {
      await api.delete(`/team/invitations/${inviteId}`);
      setSuccess('Invitation canceled');
      loadTeamData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel invitation');
    }
  };

  const handleResendInvite = async (inviteId: string) => {
    try {
      await api.post(`/team/invitations/${inviteId}/resend`);
      setSuccess('Invitation resent');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend invitation');
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return <Shield className="w-4 h-4 text-red-500" />;
      case 'manager':
        return <Shield className="w-4 h-4 text-blue-500" />;
      case 'viewer':
        return <Eye className="w-4 h-4 text-slate-500" />;
      default:
        return <User className="w-4 h-4 text-slate-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
            <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></span>
            Pending
          </span>
        );
      case 'accepted':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
            <CheckCircle className="w-3 h-3" />
            Accepted
          </span>
        );
      case 'expired':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
            Expired
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
            {status}
          </span>
        );
    }
  };

  return (
    <Layout>
      <div className="p-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-6 h-6 text-orange-600" />
              Team Management
            </h1>
            <p className="text-slate-600 mt-1">
              Invite and manage your team members
            </p>
          </div>
          <Button
            onClick={() => setShowInviteForm(!showInviteForm)}
            className="bg-slate-900 hover:bg-slate-800"
          >
            <Plus className="w-4 h-4 mr-2" />
            Invite Member
          </Button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}

        {/* Invite Form */}
        {showInviteForm && (
          <Card className="mb-8 border-orange-200">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-orange-600" />
                Invite Team Member
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleInvite} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Email Address
                    </label>
                    <Input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="colleague@company.com"
                      required
                      className="h-11"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Role
                    </label>
                    <select
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="w-full h-11 rounded-md border border-slate-300 px-3 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      <option value="viewer">Viewer - Can view only</option>
                      <option value="sales_rep">Sales Rep - Create quotes</option>
                      <option value="manager">Manager - Manage team & analytics</option>
                      <option value="admin">Admin - Full access</option>
                    </select>
                    <p className="text-xs text-slate-500 mt-1">
                      {roleDescription[inviteRole]}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <Button
                    type="submit"
                    disabled={isInviting || !inviteEmail}
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    {isInviting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Mail className="w-4 h-4 mr-2" />
                        Send Invitation
                      </>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setShowInviteForm(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Team Members */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="w-5 h-5 text-slate-600" />
              Team Members ({members.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-12 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-orange-600 mx-auto mb-4" />
                <p className="text-slate-600">Loading team members...</p>
              </div>
            ) : members.length === 0 ? (
              <div className="py-12 text-center text-slate-500">
                <Users className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                <p>No team members yet</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="py-4 flex items-center justify-between hover:bg-slate-50 -mx-6 px-6 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                        <span className="text-slate-600 font-medium">
                          {member.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{member.name}</p>
                        <p className="text-sm text-slate-500">{member.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        {getRoleIcon(member.role)}
                        <span className="text-sm text-slate-600">
                          {roleDisplay[member.role] || member.role}
                        </span>
                      </div>
                      {member.last_login && (
                        <span className="text-xs text-slate-400">
                          Last active {new Date(member.last_login).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Invitations */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Mail className="w-5 h-5 text-slate-600" />
              Pending Invitations ({invitations.filter(i => i.status === 'pending').length})
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={loadTeamData}
              className="text-slate-500"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent>
            {invitations.length === 0 ? (
              <div className="py-8 text-center text-slate-500">
                <Mail className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                <p>No invitations sent</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {invitations.map((invite) => (
                  <div
                    key={invite.id}
                    className="py-4 flex items-center justify-between hover:bg-slate-50 -mx-6 px-6 transition-colors"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-slate-900">{invite.email}</p>
                        {getStatusBadge(invite.status)}
                      </div>
                      <p className="text-sm text-slate-500">
                        {roleDisplay[invite.role] || invite.role} • 
                        Invited by {invite.invited_by_name} • 
                        {new Date(invite.created_at).toLocaleDateString()}
                      </p>
                      {invite.status === 'pending' && (
                        <p className="text-xs text-amber-600 mt-1">
                          Expires {new Date(invite.expires_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    {invite.status === 'pending' && (
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleResendInvite(invite.id)}
                          className="text-slate-600"
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Resend
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCancelInvite(invite.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <X className="w-4 h-4 mr-1" />
                          Cancel
                        </Button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Role Guide */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(roleDisplay).map(([role, label]) => (
            <div key={role} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center gap-2 mb-2">
                {getRoleIcon(role)}
                <span className="font-medium text-slate-900">{label}</span>
              </div>
              <p className="text-xs text-slate-600">
                {roleDescription[role]}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
