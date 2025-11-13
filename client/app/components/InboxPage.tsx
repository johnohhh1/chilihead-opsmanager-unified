'use client';

import { useState, useEffect } from 'react';
import {
  Mail, MailOpen, RefreshCw, Filter, Search, Settings, Loader2, AlertCircle, CheckCircle
} from 'lucide-react';

interface Email {
  thread_id: string;
  gmail_message_id: string;
  subject: string;
  sender: string;
  body_text: string;
  received_at: string;
  is_read: boolean;
  has_images: boolean;
  labels: string[];
}

interface InboxPageProps {
  onNavigate?: (page: string) => void;
}

export default function InboxPage({ onNavigate }: InboxPageProps) {
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [domains, setDomains] = useState<string[]>([]);
  const [newDomain, setNewDomain] = useState('');
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchEmails();
    fetchDomains();
    fetchStats();
  }, [filter]);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const unreadParam = filter === 'unread' ? '&unread_only=true' : '';
      const response = await fetch(`/api/backend/inbox?limit=50${unreadParam}`);
      const data = await response.json();

      if (data.success) {
        setEmails(data.emails);
      }
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDomains = async () => {
    try {
      const response = await fetch('/api/backend/settings/domains');
      const data = await response.json();
      if (data.success) {
        setDomains(data.domains);
      }
    } catch (error) {
      console.error('Failed to fetch domains:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/backend/inbox/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.inbox);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const syncInbox = async () => {
    try {
      setSyncing(true);
      const response = await fetch('/api/backend/sync-inbox', { method: 'POST' });
      const data = await response.json();

      if (data.success) {
        // Show success toast
        showToast(`Synced ${data.synced} new emails`, 'success');
        fetchEmails();
        fetchStats();
      } else {
        showToast(data.error || 'Sync failed', 'error');
      }
    } catch (error) {
      console.error('Failed to sync inbox:', error);
      showToast('Sync failed', 'error');
    } finally {
      setSyncing(false);
    }
  };

  const selectEmail = async (threadId: string) => {
    try {
      const response = await fetch(`/api/backend/inbox/${threadId}`);
      const data = await response.json();

      if (data.success) {
        setSelectedEmail(data.email);

        // Mark as read if unread
        if (!data.email.is_read) {
          await markAsRead(threadId, true);
        }
      }
    } catch (error) {
      console.error('Failed to fetch email:', error);
    }
  };

  const markAsRead = async (threadId: string, isRead: boolean) => {
    try {
      await fetch(`/api/backend/inbox/${threadId}/mark-read`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: isRead })
      });

      // Update local state
      setEmails(emails.map(email =>
        email.thread_id === threadId ? { ...email, is_read: isRead } : email
      ));

      fetchStats();
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const addDomain = async () => {
    if (!newDomain.trim()) return;

    try {
      const response = await fetch('/api/backend/settings/domains', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: newDomain.trim().toLowerCase() })
      });

      const data = await response.json();

      if (data.success) {
        setDomains(data.domains);
        setNewDomain('');
        showToast(`Domain '${newDomain}' added`, 'success');
      } else {
        showToast('Failed to add domain', 'error');
      }
    } catch (error) {
      console.error('Failed to add domain:', error);
      showToast('Failed to add domain', 'error');
    }
  };

  const removeDomain = async (domain: string) => {
    try {
      const response = await fetch('/api/backend/settings/domains', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain })
      });

      const data = await response.json();

      if (data.success) {
        setDomains(data.domains);
        showToast(`Domain '${domain}' removed`, 'success');
      }
    } catch (error) {
      console.error('Failed to remove domain:', error);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-4 py-2 rounded-lg shadow-lg z-50`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  };

  const filteredEmails = emails.filter(email =>
    email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
    email.sender.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const extractDomain = (sender: string) => {
    const match = sender.match(/@([^>]+)/);
    return match ? match[1].trim() : '';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Mail className="h-6 w-6 text-red-500" />
            <span>Inbox</span>
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            {stats && (
              <>
                {stats.total} emails ({stats.unread} unread)
              </>
            )}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Settings className="h-4 w-4" />
            <span>Domains</span>
          </button>

          <button
            onClick={syncInbox}
            disabled={syncing}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync Now'}</span>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3">Watched Domains</h3>

          {/* Add Domain */}
          <div className="flex items-center space-x-2 mb-4">
            <input
              type="text"
              value={newDomain}
              onChange={(e) => setNewDomain(e.target.value)}
              placeholder="example.com"
              className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500"
              onKeyPress={(e) => e.key === 'Enter' && addDomain()}
            />
            <button
              onClick={addDomain}
              className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg"
            >
              Add
            </button>
          </div>

          {/* Domain List */}
          <div className="space-y-2">
            {domains.map((domain) => (
              <div
                key={domain}
                className="flex items-center justify-between bg-gray-900 px-3 py-2 rounded-lg"
              >
                <span className="text-white">{domain}</span>
                <button
                  onClick={() => removeDomain(domain)}
                  className="text-red-500 hover:text-red-400 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>

          {domains.length === 0 && (
            <p className="text-gray-500 text-sm italic">
              No domains configured. Add domains to start syncing emails.
            </p>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium text-sm ${
              filter === 'all'
                ? 'bg-red-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('unread')}
            className={`px-4 py-2 rounded-lg font-medium text-sm ${
              filter === 'unread'
                ? 'bg-red-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Unread
          </button>
        </div>

        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search emails..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500"
            />
          </div>
        </div>
      </div>

      {/* Email List / View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Email List */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <Loader2 className="h-8 w-8 text-red-500 animate-spin" />
            </div>
          ) : filteredEmails.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-96 text-gray-500">
              <Mail className="h-12 w-12 mb-3" />
              <p>No emails found</p>
              {filter === 'unread' && (
                <p className="text-sm mt-1">Try viewing all emails</p>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-700">
              {filteredEmails.map((email) => (
                <div
                  key={email.thread_id}
                  onClick={() => selectEmail(email.thread_id)}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedEmail?.thread_id === email.thread_id
                      ? 'bg-gray-700'
                      : 'hover:bg-gray-750'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    {email.is_read ? (
                      <MailOpen className="h-5 w-5 text-gray-500 flex-shrink-0 mt-0.5" />
                    ) : (
                      <Mail className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className={`text-sm truncate ${email.is_read ? 'text-gray-400' : 'text-white font-medium'}`}>
                          {email.sender}
                        </p>
                        <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                          {new Date(email.received_at).toLocaleDateString()}
                        </span>
                      </div>

                      <p className={`text-sm truncate ${email.is_read ? 'text-gray-500' : 'text-gray-300'}`}>
                        {email.subject}
                      </p>

                      <p className="text-xs text-gray-600 truncate mt-1">
                        {email.body_text?.substring(0, 80)}...
                      </p>

                      <div className="flex items-center space-x-2 mt-2">
                        <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-400 rounded">
                          {extractDomain(email.sender)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Email View */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {selectedEmail ? (
            <div className="h-full flex flex-col">
              {/* Email Header */}
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-2">
                  {selectedEmail.subject}
                </h3>
                <div className="flex items-center justify-between text-sm">
                  <p className="text-gray-400">From: {selectedEmail.sender}</p>
                  <p className="text-gray-500">
                    {new Date(selectedEmail.received_at).toLocaleString()}
                  </p>
                </div>

                {selectedEmail.analysis && (
                  <div className="mt-3 flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded ${
                      selectedEmail.analysis.category === 'urgent'
                        ? 'bg-red-900 text-red-300'
                        : selectedEmail.analysis.category === 'important'
                        ? 'bg-orange-900 text-orange-300'
                        : 'bg-blue-900 text-blue-300'
                    }`}>
                      {selectedEmail.analysis.category}
                    </span>
                    <span className="text-xs text-gray-500">
                      Priority: {selectedEmail.analysis.priority_score}/100
                    </span>
                  </div>
                )}
              </div>

              {/* Email Body */}
              <div className="flex-1 overflow-y-auto p-4">
                {selectedEmail.body_html ? (
                  <div
                    className="prose prose-invert max-w-none text-gray-300"
                    dangerouslySetInnerHTML={{
                      __html: selectedEmail.body_html
                        // Remove cid: image references that won't load
                        .replace(/<img[^>]+src="cid:[^"]*"[^>]*>/gi, '<div class="bg-gray-700 text-gray-400 text-xs p-2 rounded my-2">📷 [Image removed - not available in cached email]</div>')
                        // Make external images load with error handling
                        .replace(/<img/gi, '<img style="max-width: 100%; height: auto;" onerror="this.style.display=\'none\'"')
                    }}
                  />
                ) : (
                  <pre className="whitespace-pre-wrap text-gray-300 text-sm">
                    {selectedEmail.body_text}
                  </pre>
                )}
              </div>

              {/* Actions */}
              <div className="p-4 border-t border-gray-700 flex items-center space-x-3">
                <button
                  onClick={() => markAsRead(selectedEmail.thread_id, !selectedEmail.is_read)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
                >
                  Mark as {selectedEmail.is_read ? 'Unread' : 'Read'}
                </button>

                {selectedEmail.analysis?.suggested_tasks?.length > 0 && (
                  <button
                    onClick={() => {
                      // TODO: Integrate with existing task system
                      showToast('Task extraction coming soon!', 'success');
                    }}
                    className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm"
                  >
                    Extract Tasks
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-96 text-gray-500">
              <div className="text-center">
                <Mail className="h-12 w-12 mx-auto mb-3" />
                <p>Select an email to view</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
