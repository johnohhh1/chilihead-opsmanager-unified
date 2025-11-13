'use client';

/**
 * SmartInboxPage - Unified email interface combining Inbox + Triage
 *
 * Features from InboxPage:
 * - Gmail sync with EmailCache
 * - Two-column layout (list + detail)
 * - HTML email rendering
 * - Read/unread tracking
 * - Domain management
 *
 * Features from TriagePage:
 * - AI analysis with model selection
 * - Priority scoring and categorization
 * - Task extraction to Todo list
 * - Daily Brief integration
 * - Deadline scanner
 * - Acknowledged emails tracking
 * - Agent memory integration
 */

import { useState, useEffect } from 'react';
import {
  Mail, MailOpen, RefreshCw, Filter, Search, Settings, Loader2, AlertCircle,
  CheckCircle, Brain, Zap, Calendar, Clock, ChevronDown, ChevronUp, Plus,
  Eye, EyeOff, Sparkles, ArrowRight, X, Trash2, Check, Download, Image as ImageIcon
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import DailyBriefModal from './DailyBriefModal';

interface Email {
  thread_id: string;
  gmail_message_id: string;
  subject: string;
  sender: string;
  body_text: string;
  body_html?: string;
  received_at: string;
  is_read: boolean;
  has_images: boolean;
  labels: string[];
  state?: {
    acknowledged?: boolean;
    analyzed?: boolean;
    tasks_added?: string[];
  };
  analysis?: {
    category: string;
    priority_score: number;
    suggested_tasks?: any[];
  };
}

interface SmartInboxPageProps {
  onAddToTodo: (items: any[], threadId?: string) => Promise<void>;
  onNavigate?: (page: string) => void;
}

export default function SmartInboxPage({ onAddToTodo, onNavigate }: SmartInboxPageProps) {
  // Email state
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Filter state
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [hideAcknowledged, setHideAcknowledged] = useState(false);

  // Settings state
  const [showSettings, setShowSettings] = useState(false);
  const [domains, setDomains] = useState<string[]>([]);
  const [newDomain, setNewDomain] = useState('');
  const [stats, setStats] = useState<any>(null);

  // AI Model state
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<string>("unknown");

  // Daily Brief state
  const [showDailyBrief, setShowDailyBrief] = useState(false);
  const [digest, setDigest] = useState<string>('');
  const [digestGeneratedAt, setDigestGeneratedAt] = useState<string>('');
  const [digestSessionId, setDigestSessionId] = useState<string>('');

  useEffect(() => {
    fetchEmails();
    fetchDomains();
    fetchStats();
    loadModels();
  }, [filter, hideAcknowledged]);

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

  const loadModels = async () => {
    setModelsLoading(true);
    try {
      const response = await fetch('/api/backend/models/list', {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
        setOllamaStatus(data.ollama_status || "unknown");
        const savedModel = localStorage.getItem('preferred-ai-model');
        if (savedModel) {
          setSelectedModel(savedModel);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      setOllamaStatus("error");
    } finally {
      setModelsLoading(false);
    }
  };

  const syncInbox = async () => {
    try {
      setSyncing(true);
      const response = await fetch('/api/backend/sync-inbox', { method: 'POST' });
      const data = await response.json();

      if (data.success) {
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

  const fetchDigest = async () => {
    try {
      // Add timestamp to force fresh fetch (no caching)
      const response = await fetch(`/api/backend/daily-digest?t=${Date.now()}&model=${selectedModel}`);
      const data = await response.json();
      setDigest(data.digest);
      setDigestGeneratedAt(data.generated_at || new Date().toISOString());
      setDigestSessionId(data.session_id || ''); // Store the session ID
      setShowDailyBrief(true);
    } catch (error) {
      console.error('Failed to fetch digest:', error);
      showToast('Failed to fetch daily brief', 'error');
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

  const analyzeEmail = async (threadId: string) => {
    try {
      setAnalyzing(true);
      const response = await fetch('/api/backend/smart-triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId, model: selectedModel })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Update selected email with raw analysis data
      setSelectedEmail({ ...selectedEmail, analysis: data });

      // Also update the emails list
      setEmails(emails.map(email =>
        email.thread_id === threadId ? { ...email, analysis: data, state: { ...email.state, analyzed: true } } : email
      ));

      showToast(data.cached ? 'Analysis loaded from cache' : 'Analysis complete', 'success');
    } catch (error) {
      console.error('Failed to analyze email:', error);
      showToast('Analysis failed', 'error');
    } finally {
      setAnalyzing(false);
    }
  };

  const markAsRead = async (threadId: string, isRead: boolean) => {
    try {
      await fetch(`/api/backend/inbox/${threadId}/mark-read`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_read: isRead })
      });

      // Update emails list
      setEmails(emails.map(email =>
        email.thread_id === threadId ? { ...email, is_read: isRead } : email
      ));

      // Update selected email if it's the one being marked
      if (selectedEmail && selectedEmail.thread_id === threadId) {
        setSelectedEmail({ ...selectedEmail, is_read: isRead });
      }

      fetchStats();
      showToast(isRead ? 'Marked as read' : 'Marked as unread', 'success');
    } catch (error) {
      console.error('Failed to mark as read:', error);
      showToast('Failed to update status', 'error');
    }
  };

  const extractImages = (html: string): string[] => {
    if (!html) return [];
    const imgRegex = /<img[^>]+src="([^"]+)"/gi;
    const images: string[] = [];
    let match;
    while ((match = imgRegex.exec(html)) !== null) {
      const src = match[1];
      // Only include http/https images (skip cid: and data: URLs)
      if (src.startsWith('http://') || src.startsWith('https://')) {
        images.push(src);
      }
    }
    return images;
  };

  const acknowledgeEmail = async (threadId: string) => {
    try {
      const response = await fetch(`/api/backend/emails/${threadId}/acknowledge`, {
        method: 'POST'
      });

      if (response.ok) {
        setEmails(emails.map(email =>
          email.thread_id === threadId
            ? { ...email, state: { ...email.state, acknowledged: true } }
            : email
        ));
        showToast('Email acknowledged', 'success');
      }
    } catch (error) {
      console.error('Failed to acknowledge email:', error);
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

  const filteredEmails = emails
    .filter(email => {
      if (hideAcknowledged && email.state?.acknowledged) return false;
      return (
        email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
        email.sender.toLowerCase().includes(searchTerm.toLowerCase())
      );
    });

  const extractDomain = (sender: string) => {
    const match = sender.match(/@([^>]+)/);
    return match ? match[1].trim() : '';
  };

  const getPriorityColor = (score?: number) => {
    if (!score) return 'bg-gray-700 text-gray-300';
    if (score >= 80) return 'bg-red-900 text-red-300';
    if (score >= 60) return 'bg-orange-900 text-orange-300';
    return 'bg-blue-900 text-blue-300';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Sparkles className="h-6 w-6 text-red-500" />
            <span>Smart Inbox</span>
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
          {/* AI Model Selector */}
          <div className="flex items-center space-x-2">
            <Brain className="h-4 w-4 text-purple-400" />
            <select
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
                localStorage.setItem('preferred-ai-model', e.target.value);
              }}
              className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:ring-2 focus:ring-purple-500"
            >
              {availableModels.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          {/* Daily Brief Button */}
          <button
            onClick={fetchDigest}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Calendar className="h-4 w-4" />
            <span>Daily Brief</span>
          </button>

          {/* Settings */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Settings className="h-4 w-4" />
            <span>Domains</span>
          </button>

          {/* Sync Button */}
          <button
            onClick={syncInbox}
            disabled={syncing}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Syncing...' : 'Sync'}</span>
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-4">
          <h3 className="text-lg font-semibold text-white">Settings</h3>

          {/* AI Model Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              AI Model for Analysis
            </label>
            <select
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
                localStorage.setItem('preferred-ai-model', e.target.value);
              }}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white"
            >
              {availableModels.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} {model.provider === 'ollama' ? '(Local)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Domain Management */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Watched Domains
            </label>
            <div className="flex items-center space-x-2 mb-2">
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
          </div>
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
          <button
            onClick={() => setHideAcknowledged(!hideAcknowledged)}
            className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center space-x-2 ${
              hideAcknowledged
                ? 'bg-red-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {hideAcknowledged ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            <span>Hide Ack'd</span>
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
            </div>
          ) : (
            <div className="divide-y divide-gray-700 max-h-[800px] overflow-y-auto">
              {filteredEmails.map((email) => (
                <div
                  key={email.thread_id}
                  onClick={() => selectEmail(email.thread_id)}
                  className={`p-4 cursor-pointer hover:bg-gray-700 transition-colors ${
                    selectedEmail?.thread_id === email.thread_id ? 'bg-gray-700' : ''
                  } ${!email.is_read ? 'bg-gray-750' : ''}`}
                >
                  <div className="flex items-start space-x-3">
                    {email.is_read ? (
                      <MailOpen className="h-5 w-5 text-gray-500 flex-shrink-0 mt-1" />
                    ) : (
                      <Mail className="h-5 w-5 text-red-500 flex-shrink-0 mt-1" />
                    )}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-sm font-medium text-white truncate">
                          {email.sender.split('<')[0].trim()}
                        </p>
                        <span className="text-xs text-gray-500 ml-2">
                          {new Date(email.received_at).toLocaleDateString()}
                        </span>
                      </div>

                      <p className="text-sm font-medium text-gray-200 truncate mb-1">
                        {email.subject}
                      </p>

                      <p className="text-xs text-gray-400 truncate mb-2">
                        {email.body_text?.substring(0, 80)}...
                      </p>

                      <div className="flex items-center space-x-2">
                        <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-400 rounded">
                          {extractDomain(email.sender)}
                        </span>
                        {email.state?.acknowledged && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {email.analysis && (
                          <span className={`text-xs px-2 py-0.5 rounded ${getPriorityColor(email.analysis.priority_score)}`}>
                            {email.analysis.priority_score}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Email Detail View */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {selectedEmail ? (
            <div className="h-full flex flex-col max-h-[800px]">
              {/* Email Header */}
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white mb-2">
                  {selectedEmail.subject}
                </h3>
                <div className="flex items-center justify-between text-sm mb-2">
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
                {/* Images Section */}
                {selectedEmail.has_images && selectedEmail.body_html && (
                  (() => {
                    const images = extractImages(selectedEmail.body_html);
                    if (images.length > 0) {
                      return (
                        <div className="mb-4 p-3 bg-gray-700 rounded-lg border border-gray-600">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-sm font-semibold text-white flex items-center">
                              <ImageIcon className="h-4 w-4 mr-2 text-blue-400" />
                              {images.length} Image{images.length > 1 ? 's' : ''} Found
                            </h4>
                          </div>
                          <div className="space-y-2">
                            {images.map((imgUrl, idx) => (
                              <div key={idx} className="flex items-center justify-between text-xs bg-gray-800 p-2 rounded">
                                <span className="text-gray-400 truncate flex-1 mr-2">
                                  {imgUrl.length > 60 ? imgUrl.substring(0, 60) + '...' : imgUrl}
                                </span>
                                <a
                                  href={imgUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center space-x-1 px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
                                >
                                  <Download className="h-3 w-3" />
                                  <span>Open</span>
                                </a>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })()
                )}

                {selectedEmail.body_html ? (
                  <div
                    className="prose prose-invert max-w-none text-gray-300"
                    dangerouslySetInnerHTML={{
                      __html: selectedEmail.body_html
                        .replace(/<img[^>]+src="cid:[^"]*"[^>]*>/gi, '<div class="bg-gray-700 text-gray-400 text-xs p-2 rounded my-2">📷 [Image removed - check above for downloadable images]</div>')
                        .replace(/<img/gi, '<img style="max-width: 100%; height: auto;" onerror="this.style.display=\'none\'"')
                    }}
                  />
                ) : (
                  <pre className="whitespace-pre-wrap text-gray-300 text-sm">
                    {selectedEmail.body_text}
                  </pre>
                )}

                {/* AI Analysis */}
                {selectedEmail.analysis && (
                  <div className="mt-6 pt-6 border-t border-gray-700">
                    <h4 className="text-md font-semibold text-white mb-3 flex items-center">
                      <Brain className="h-5 w-5 mr-2 text-purple-400" />
                      AI Analysis
                    </h4>
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {selectedEmail.analysis.analysis || ''}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="p-4 border-t border-gray-700 flex items-center space-x-3 flex-wrap gap-2">
                <button
                  onClick={() => markAsRead(selectedEmail.thread_id, !selectedEmail.is_read)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
                >
                  {selectedEmail.is_read ? 'Mark Unread' : 'Mark Read'}
                </button>

                <button
                  onClick={() => analyzeEmail(selectedEmail.thread_id)}
                  disabled={analyzing}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-sm flex items-center space-x-2 disabled:opacity-50"
                >
                  <Brain className="h-4 w-4" />
                  <span>
                    {analyzing ? 'Analyzing...' : selectedEmail.analysis ? 'Re-analyze' : 'Analyze'}
                  </span>
                </button>

                {!selectedEmail.state?.acknowledged && (
                  <button
                    onClick={() => acknowledgeEmail(selectedEmail.thread_id)}
                    className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm flex items-center space-x-2"
                  >
                    <Check className="h-4 w-4" />
                    <span>Acknowledge</span>
                  </button>
                )}

                {selectedEmail.analysis?.suggested_tasks?.length > 0 && (
                  <button
                    onClick={async () => {
                      await onAddToTodo(selectedEmail.analysis.suggested_tasks, selectedEmail.thread_id);
                      showToast('Tasks added to todo list', 'success');
                    }}
                    className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm flex items-center space-x-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Add Tasks</span>
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

      {/* Daily Brief Modal */}
      {showDailyBrief && (
        <DailyBriefModal
          digest={digest}
          generatedAt={digestGeneratedAt}
          sessionId={digestSessionId}
          onClose={() => setShowDailyBrief(false)}
        />
      )}
    </div>
  );
}
