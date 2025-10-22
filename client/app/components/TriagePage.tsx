'use client';

import { useState, useEffect } from 'react';
import {
  RefreshCw, Calendar, AlertTriangle, Clock,
  ChevronDown, ChevronUp, Plus, Brain, Zap,
  Mail, User, Tag, ArrowRight, Sparkles, MessageSquare,
  Phone, Link, CheckCircle, Check, X, Filter, Eye, EyeOff,
  Settings, Trash2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface EmailThread {
  id: string;
  subject: string;
  from: string;
  snippet: string;
  date: string;
  priority_score: number;
  labels: string[];
  state?: {
    acknowledged?: boolean;
    analyzed?: boolean;
    tasks_added?: string[];
  };
}

interface TriagePageProps {
  onAddToTodo: (items: any[], threadId?: string) => Promise<void>;
  onNavigate?: (page: 'triage' | 'todo' | 'delegations') => void;
}

interface WatchConfig {
  priority_senders: string[];
  priority_domains: string[];
  keywords: string[];
  excluded_subjects: string[];
  auto_flag_as_important: boolean;
  include_unread_only: boolean;
}

export default function TriagePage({ onAddToTodo, onNavigate }: TriagePageProps) {
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [expandedThread, setExpandedThread] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<Map<string, any>>(new Map());
  const [timeRange, setTimeRange] = useState('today');
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [showDigest, setShowDigest] = useState(false);
  const [digest, setDigest] = useState<string>('');
  const [hideAcknowledged, setHideAcknowledged] = useState(false);
  const [showDeadlines, setShowDeadlines] = useState(false);
  const [deadlineReport, setDeadlineReport] = useState('');
  const [deadlines, setDeadlines] = useState<any[]>([]);
  const [deadlineLoading, setDeadlineLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [authUrl, setAuthUrl] = useState<string>('');

  // Model selection state
  const [selectedModel, setSelectedModel] = useState<string>('gpt-4o');
  const [availableModels, setAvailableModels] = useState<any[]>([]);

  // Load available AI models
  const loadModels = async () => {
    try {
      const response = await fetch('/api/backend/models/list');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models || []);
        // Load saved model preference
        const savedModel = localStorage.getItem('preferred-ai-model');
        if (savedModel) {
          setSelectedModel(savedModel);
        }
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  // Handle model selection change
  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
    localStorage.setItem('preferred-ai-model', modelId);
  };

  // Preferences panel state
  const [showPreferences, setShowPreferences] = useState(false);
  const [watchConfig, setWatchConfig] = useState<WatchConfig>({
    priority_senders: [],
    priority_domains: [],
    keywords: [],
    excluded_subjects: [],
    auto_flag_as_important: true,
    include_unread_only: false
  });
  const [newSender, setNewSender] = useState('');
  const [newDomain, setNewDomain] = useState('');
  const [newExclusion, setNewExclusion] = useState('');

  // Load watch configuration
  const loadWatchConfig = async () => {
    try {
      const response = await fetch('/api/backend/watch-config');
      const data = await response.json();
      setWatchConfig(data);
    } catch (error) {
      console.error('Failed to load watch config:', error);
    }
  };

  // Add sender to watch list
  const addSender = async () => {
    if (!newSender.trim()) return;
    
    try {
      const response = await fetch(`/api/backend/watch-config/add-sender?email=${encodeURIComponent(newSender)}`, {
        method: 'POST'
      });
      const data = await response.json();
      setWatchConfig(data.config);
      setNewSender('');
    } catch (error) {
      console.error('Failed to add sender:', error);
    }
  };

  // Add domain to watch list
  const addDomain = async () => {
    if (!newDomain.trim()) return;
    
    try {
      const response = await fetch(`/api/backend/watch-config/add-domain?domain=${encodeURIComponent(newDomain)}`, {
        method: 'POST'
      });
      const data = await response.json();
      setWatchConfig(data.config);
      setNewDomain('');
    } catch (error) {
      console.error('Failed to add domain:', error);
    }
  };

  // Remove sender from watch list
  const removeSender = async (email: string) => {
    try {
      const response = await fetch(`/api/backend/watch-config/remove-sender?email=${encodeURIComponent(email)}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      setWatchConfig(data.config);
    } catch (error) {
      console.error('Failed to remove sender:', error);
    }
  };

  // Remove domain from watch list
  const removeDomain = async (domain: string) => {
    try {
      const response = await fetch(`/api/backend/watch-config/remove-domain?domain=${encodeURIComponent(domain)}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      setWatchConfig(data.config);
    } catch (error) {
      console.error('Failed to remove domain:', error);
    }
  };

  // Add exclusion pattern
  const addExclusion = async () => {
    if (!newExclusion.trim()) return;
    
    try {
      const response = await fetch(`/api/backend/watch-config/add-exclusion?pattern=${encodeURIComponent(newExclusion)}`, {
        method: 'POST'
      });
      const data = await response.json();
      setWatchConfig(data.config);
      setNewExclusion('');
    } catch (error) {
      console.error('Failed to add exclusion:', error);
    }
  };

  // Remove exclusion pattern
  const removeExclusion = async (pattern: string) => {
    try {
      const response = await fetch(`/api/backend/watch-config/remove-exclusion?pattern=${encodeURIComponent(pattern)}`, {
        method: 'DELETE'
      });
      const data = await response.json();
      setWatchConfig(data.config);
    } catch (error) {
      console.error('Failed to remove exclusion:', error);
    }
  };

  // Check authentication status
  const checkAuth = async () => {
    try {
      const params = new URLSearchParams({
        watched_only: 'true',
        priority_sort: 'true',
        max_results: '1',
        time_range: timeRange
      });
      
      const response = await fetch(`/api/backend/threads?${params}`);
      
      if (response.status === 401) {
        setIsAuthenticated(false);
        // Get auth URL
        const authResponse = await fetch('/api/backend/auth/url');
        const authData = await authResponse.json();
        setAuthUrl(authData.auth_url);
        setLoading(false);
        return false;
      }
      
      setIsAuthenticated(true);
      return true;
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setLoading(false);
      return false;
    }
  };

  // Fetch threads
  const fetchThreads = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        watched_only: 'true',
        priority_sort: 'true',
        max_results: '100',
        time_range: showDatePicker && dateFrom && dateTo ? 'custom' : timeRange
      });
      
      // Add custom dates if date picker is active
      if (showDatePicker && dateFrom && dateTo) {
        params.set('date_from', dateFrom);
        params.set('date_to', dateTo);
      }
      
      const response = await fetch(`/api/backend/threads?${params}`);
      
      if (response.status === 401) {
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      setThreads(data.threads || []);
    } catch (error) {
      console.error('Failed to fetch threads:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get smart AI analysis - OPTIMIZED: Don't refetch all threads
  const analyzeThread = async (threadId: string) => {
    setAnalyzing(true);
    try {
      const response = await fetch('/api/backend/smart-triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: threadId,
          model: selectedModel // Include selected AI model
        })
      });
      
      const data = await response.json();
      setAnalyses(prev => new Map(prev).set(threadId, data));
      setExpandedThread(threadId);
      
      // OPTIMIZED: Update just this thread's state instead of refetching everything
      setThreads(prev => prev.map(thread => 
        thread.id === threadId 
          ? { ...thread, state: { ...thread.state, analyzed: true } }
          : thread
      ));
    } catch (error) {
      console.error('Failed to analyze thread:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  // Acknowledge email - OPTIMIZED: Don't refetch all threads
  const acknowledgeEmail = async (threadId: string) => {
    try {
      const response = await fetch('/api/backend/state/acknowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId })
      });
      
      if (response.ok) {
        // OPTIMIZED: Update just this thread's state
        setThreads(prev => prev.map(thread => 
          thread.id === threadId 
            ? { ...thread, state: { ...thread.state, acknowledged: true } }
            : thread
        ));
      }
    } catch (error) {
      console.error('Failed to acknowledge email:', error);
    }
  };

  // Get daily digest
  const fetchDigest = async () => {
    try {
      // Add timestamp to force fresh fetch (no caching)
      const response = await fetch(`/api/backend/daily-digest?t=${Date.now()}&model=${selectedModel}`);
      const data = await response.json();
      setDigest(data.digest);
      setShowDigest(true);
    } catch (error) {
      console.error('Failed to get digest:', error);
    }
  };

  // Get deadline scan
  const fetchDeadlines = async () => {
    setDeadlineLoading(true);
    try {
      const response = await fetch(`/api/backend/deadline-scan?model=${selectedModel}`);
      const data = await response.json();
      setDeadlineReport(data.report || 'No deadlines found');
      setDeadlines(data.deadlines || []);
      setShowDeadlines(true);
    } catch (error) {
      console.error('Failed to fetch deadlines:', error);
      setDeadlineReport('Failed to load deadline scan');
    } finally {
      setDeadlineLoading(false);
    }
  };

  const addDeadlineToCalendar = async (deadline: any) => {
    try {
      const response = await fetch('/api/backend/calendar/create-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: deadline.calendar_title,
          date: deadline.calendar_date,
          time: deadline.calendar_time || '10:00 AM',
          description: `${deadline.summary}\n\nEmail: ${deadline.gmail_link || ''}`,
          location: 'Chili\'s - Auburn Hills #605',
          reminder_days: 3
        })
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ Calendar event created!\n\n${deadline.calendar_title}\n${deadline.calendar_date} at ${deadline.calendar_time}\n\nView in Google Calendar: ${data.event_link}`);
      } else {
        alert(`❌ Failed to create calendar event:\n${data.error}`);
      }
    } catch (error) {
      console.error('Failed to create calendar event:', error);
      alert('❌ Failed to create calendar event. Please try again.');
    }
  };

  useEffect(() => {
    loadModels(); // Load available AI models first
  }, []); // Run only once on mount

  useEffect(() => {
    const initAuth = async () => {
      const authenticated = await checkAuth();
      if (authenticated) {
        loadWatchConfig();
        fetchThreads();
        // Don't auto-fetch digest on page load - user can click button
      }
    };
    initAuth();
  }, [timeRange, dateFrom, dateTo]);

  // Parse email
  const parseEmail = (from: string) => {
    if (!from) return { name: 'Unknown', email: '' };
    const match = from.match(/(.*?)<(.+?)>/);
    if (match) {
      return { name: match[1].trim() || match[2], email: match[2] };
    }
    return { name: from, email: from };
  };

  // Get priority indicator
  const getPriorityIndicator = (score: number) => {
    if (score >= 75) return { icon: '🔴', color: 'text-red-600', bg: 'bg-red-50' };
    if (score >= 50) return { icon: '🟡', color: 'text-orange-600', bg: 'bg-orange-50' };
    if (score >= 25) return { icon: '🟢', color: 'text-green-600', bg: 'bg-green-50' };
    return { icon: '⚪', color: 'text-gray-600', bg: 'bg-white' };
  };

  // Make URLs clickable in text
  const linkifyText = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);
    
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 underline"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

  // Add individual task - OPTIMIZED: Update thread state directly
  const addSingleTask = async (task: any, threadId: string) => {
    await onAddToTodo([task], threadId);
    
    // Update thread to show task was added
    setThreads(prev => prev.map(thread => {
      if (thread.id === threadId) {
        const currentTasks = thread.state?.tasks_added || [];
        return {
          ...thread,
          state: {
            ...thread.state,
            tasks_added: [...currentTasks, task.action]
          }
        };
      }
      return thread;
    }));
  };

  // Add all tasks - OPTIMIZED: Update thread state directly
  const addAllTasks = async (tasks: any[], threadId: string) => {
    await onAddToTodo(tasks, threadId);
    
    // Update thread to show all tasks were added
    setThreads(prev => prev.map(thread => {
      if (thread.id === threadId) {
        return {
          ...thread,
          state: {
            ...thread.state,
            tasks_added: tasks.map(t => t.action)
          }
        };
      }
      return thread;
    }));
  };

  // Filter threads based on acknowledged status
  const visibleThreads = hideAcknowledged 
    ? threads.filter(t => !t.state?.acknowledged)
    : threads;

  // Show login screen if not authenticated
  if (isAuthenticated === false) {
    return (
      <div className="space-y-6">
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-12 text-center max-w-2xl mx-auto">
          <div className="mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-red-500 to-orange-500 rounded-full mb-4">
              <Mail className="h-10 w-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Connect Your Gmail</h2>
            <p className="text-gray-300 mb-8">
              Sign in with Google to enable AI-powered email triage and smart inbox management.
            </p>
          </div>

          <div className="space-y-4">
            <a
              href={authUrl}
              className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-red-500 to-orange-500 text-white font-bold rounded-lg hover:from-red-600 hover:to-orange-600 shadow-lg transform hover:scale-105 transition-all space-x-3"
            >
              <Mail className="h-6 w-6" />
              <span>Sign in with Google</span>
            </a>

            <div className="mt-8 p-6 bg-gray-700 rounded-lg text-left">
              <h3 className="font-semibold text-white mb-3">What you'll get:</h3>
              <ul className="space-y-2 text-sm text-gray-300">
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span><strong>AI Email Analysis:</strong> GPT-4 understands context and extracts action items</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span><strong>Priority Scoring:</strong> Automatically sorts emails by importance</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span><strong>Smart Task Creation:</strong> One-click to add emails to your todo list</span>
                </li>
                <li className="flex items-start">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <span><strong>Daily Digest:</strong> Get a summary of what needs your attention</span>
                </li>
              </ul>
            </div>

            <p className="text-xs text-gray-400 mt-6">
              🔒 Your data is secure. We only access emails you choose to analyze.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      {onNavigate && (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-3">
          <nav className="flex space-x-2">
            <button
              onClick={() => onNavigate('triage')}
              className="px-4 py-2 rounded-lg font-medium text-sm bg-red-500 text-white"
            >
              📧 Email Triage
            </button>
            <button
              onClick={() => onNavigate('todo')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              ✓ Todo List
            </button>
            <button
              onClick={() => onNavigate('delegations')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              🌶️ Delegations
            </button>
          </nav>
        </div>
      )}

      {/* Preferences Panel */}
      {showPreferences && (
        <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white flex items-center">
              <Settings className="h-6 w-6 mr-2" />
              Watch Configuration
            </h3>
            <button
              onClick={() => setShowPreferences(false)}
              className="text-gray-400 hover:text-gray-300"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Priority Senders */}
            <div>
              <h4 className="font-semibold text-white mb-3">Priority Senders</h4>
              <div className="flex space-x-2 mb-3">
                <input
                  type="email"
                  value={newSender}
                  onChange={(e) => setNewSender(e.target.value)}
                  placeholder="Enter email address"
                  className="flex-1 px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent placeholder-gray-400"
                  onKeyPress={(e) => e.key === 'Enter' && addSender()}
                />
                <button
                  onClick={addSender}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center space-x-1"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add</span>
                </button>
              </div>
              <div className="space-y-2">
                {watchConfig.priority_senders.map((sender) => (
                  <div key={sender} className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded-lg">
                    <span className="text-sm text-gray-300">{sender}</span>
                    <button
                      onClick={() => removeSender(sender)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {watchConfig.priority_senders.length === 0 && (
                  <p className="text-sm text-gray-400 italic">No priority senders configured</p>
                )}
              </div>
            </div>

            {/* Priority Domains */}
            <div>
              <h4 className="font-semibold text-white mb-3">Priority Domains</h4>
              <div className="flex space-x-2 mb-3">
                <input
                  type="text"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  placeholder="Enter domain (e.g., brinker.com)"
                  className="flex-1 px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent placeholder-gray-400"
                  onKeyPress={(e) => e.key === 'Enter' && addDomain()}
                />
                <button
                  onClick={addDomain}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center space-x-1"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add</span>
                </button>
              </div>
              <div className="space-y-2">
                {watchConfig.priority_domains.map((domain) => (
                  <div key={domain} className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded-lg">
                    <span className="text-sm text-gray-300">{domain}</span>
                    <button
                      onClick={() => removeDomain(domain)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {watchConfig.priority_domains.length === 0 && (
                  <p className="text-sm text-gray-400 italic">No priority domains configured</p>
                )}
              </div>
            </div>

            {/* Excluded Subject Patterns */}
            <div>
              <h4 className="font-semibold text-white mb-3">Excluded Subject Patterns</h4>
              <p className="text-xs text-gray-400 mb-3">Emails with these phrases in the subject will be filtered out</p>
              <div className="flex space-x-2 mb-3">
                <input
                  type="text"
                  value={newExclusion}
                  onChange={(e) => setNewExclusion(e.target.value)}
                  placeholder="e.g., FW: FYI:, Task Policies"
                  className="flex-1 px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent placeholder-gray-400"
                  onKeyPress={(e) => e.key === 'Enter' && addExclusion()}
                />
                <button
                  onClick={addExclusion}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium flex items-center space-x-1"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add</span>
                </button>
              </div>
              <div className="space-y-2">
                {watchConfig.excluded_subjects.map((pattern) => (
                  <div key={pattern} className="flex items-center justify-between bg-gray-700 px-3 py-2 rounded-lg border border-red-600">
                    <span className="text-sm text-gray-300">{pattern}</span>
                    <button
                      onClick={() => removeExclusion(pattern)}
                      className="text-red-400 hover:text-red-300"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                {watchConfig.excluded_subjects.length === 0 && (
                  <p className="text-sm text-gray-400 italic">No exclusions configured</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Daily Digest Banner */}
      {showDigest && digest && (
        <div className="bg-gradient-to-r from-blue-900 to-blue-800 text-white rounded-xl shadow-lg p-6 border border-blue-800">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-3 flex items-center">
                <Sparkles className="h-6 w-6 mr-2" />
                Your Daily Operations Brief
              </h3>
              <div className="text-sm opacity-90 prose prose-sm max-w-none prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {digest || 'No digest available'}
                </ReactMarkdown>
              </div>
            </div>
            <button
              onClick={() => setShowDigest(false)}
              className="text-white/70 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Deadline Scanner Results */}
      {showDeadlines && deadlineReport && (
        <div className="bg-gradient-to-r from-orange-600 to-red-600 text-white rounded-xl shadow-lg p-6 border border-orange-700">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-xl font-bold mb-3 flex items-center">
                <Calendar className="h-6 w-6 mr-2" />
                Deadline Scan Report
              </h3>
              <div className="text-sm opacity-90 prose prose-sm max-w-none prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {deadlineReport || 'No deadlines found'}
                </ReactMarkdown>
              </div>

              {/* Add to Calendar Buttons */}
              {deadlines.length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/20">
                  <h4 className="text-sm font-bold mb-2">Quick Actions:</h4>
                  <div className="space-y-2">
                    {deadlines.map((deadline, idx) => (
                      <button
                        key={idx}
                        onClick={() => addDeadlineToCalendar(deadline)}
                        className="block w-full text-left px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span>#{deadline.number}: {deadline.calendar_title}</span>
                          <Calendar className="h-4 w-4" />
                        </div>
                        <div className="text-xs opacity-75 mt-1">
                          {deadline.calendar_date} at {deadline.calendar_time}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={() => setShowDeadlines(false)}
              className="text-white/70 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Smart Actions Bar */}
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-bold text-white">Smart Email Triage</h2>

            <div className="flex items-center space-x-2 text-sm text-gray-300">
              <MessageSquare className="h-4 w-4" />
              <span>AI understands context, not just keywords</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 flex-wrap gap-2">
            {/* DATE PICKER / TIME RANGE TOGGLE */}
            <button
              onClick={() => setShowDatePicker(!showDatePicker)}
              className={`px-3 py-2 rounded-lg font-medium text-sm flex items-center space-x-2 ${
                showDatePicker ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Calendar className="h-4 w-4" />
              <span>{showDatePicker ? 'Custom Dates' : 'Preset Range'}</span>
            </button>

            {/* EITHER SHOW DATE PICKER OR PRESET DROPDOWN */}
            {showDatePicker ? (
              <>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg text-sm"
                  placeholder="From"
                />
                <span className="text-gray-400">to</span>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="px-3 py-2 border border-gray-600 bg-gray-700 text-white rounded-lg text-sm"
                  placeholder="To"
                />
              </>
            ) : (
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm font-medium text-gray-300 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                <option value="today">📅 Today</option>
                <option value="yesterday">📅 Yesterday</option>
                <option value="week">📅 This Week</option>
                <option value="month">📅 This Month</option>
                <option value="all">📅 All Time</option>
              </select>
            )}

            {/* PREFERENCES BUTTON */}
            <button
              onClick={() => setShowPreferences(!showPreferences)}
              className="px-3 py-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 font-medium text-sm flex items-center space-x-2"
            >
              <Settings className="h-4 w-4" />
              <span>Settings</span>
            </button>

            {/* Hide Acknowledged Toggle */}
            <button
              onClick={() => setHideAcknowledged(!hideAcknowledged)}
              className={`px-3 py-2 rounded-lg font-medium text-sm flex items-center space-x-2 transition-colors ${
                hideAcknowledged
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {hideAcknowledged ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              <span>{hideAcknowledged ? 'Show All' : 'Hide Done'}</span>
            </button>

            {/* AI Model Selector */}
            <div className="flex items-center space-x-2">
              <Brain className="h-4 w-4 text-gray-400" />
              <select
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                className="bg-gray-700 text-white text-sm px-3 py-2 rounded-lg border border-gray-600 hover:bg-gray-600 font-medium min-w-[200px]"
              >
                {availableModels.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                    {model.default ? ' (Default)' : ''}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={fetchDigest}
              className="px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm"
            >
              Daily Brief
            </button>

            <button
              onClick={fetchDeadlines}
              disabled={deadlineLoading}
              className="px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium text-sm flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Calendar className="h-4 w-4" />
              <span>{deadlineLoading ? 'Scanning...' : 'Deadline Scan'}</span>
            </button>

            <button
              onClick={fetchThreads}
              className="p-2 hover:bg-gray-700 rounded-lg"
            >
              <RefreshCw className={`h-5 w-5 text-gray-300 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Email List with Smart Analysis */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-8 text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-gray-400" />
            <p className="text-gray-300">Loading emails...</p>
          </div>
        ) : visibleThreads.length === 0 ? (
          <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-8 text-center">
            <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-500" />
            <p className="text-lg font-medium text-white">
              {hideAcknowledged && threads.length > 0
                ? 'All emails acknowledged!'
                : 'All caught up!'}
            </p>
            <p className="text-sm text-gray-400 mt-2">
              {hideAcknowledged && threads.length > 0
                ? 'Click "Show All" to see acknowledged emails'
                : 'No urgent emails need your attention'}
            </p>
          </div>
        ) : (
          visibleThreads.map((thread) => {
            const { name, email } = parseEmail(thread.from);
            const isExpanded = expandedThread === thread.id;
            const analysis = analyses.get(thread.id);
            const priority = getPriorityIndicator(thread.priority_score);
            const isUnread = thread.labels.includes('UNREAD');
            const isAcknowledged = thread.state?.acknowledged || false;
            const isAnalyzed = thread.state?.analyzed || false;
            const hasTasksAdded = (thread.state?.tasks_added?.length || 0) > 0;

            return (
              <div
                key={thread.id}
                className={`bg-gray-800 rounded-xl shadow-sm border border-gray-700 overflow-hidden transition-all ${
                  isExpanded ? 'ring-2 ring-red-500' : ''
                } ${isAcknowledged ? 'opacity-60' : ''}`}
              >
                <div className={`p-4 ${isAcknowledged ? 'bg-gray-900' : 'bg-gray-800'}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Priority and Status */}
                      <div className="flex items-center space-x-2 mb-2 flex-wrap gap-1">
                        <span className="text-2xl">{priority.icon}</span>
                        {isUnread && (
                          <span className="px-2 py-1 text-xs font-bold bg-blue-500 text-white rounded">
                            NEW
                          </span>
                        )}
                        {isAcknowledged && (
                          <span className="px-2 py-1 text-xs font-bold bg-green-500 text-white rounded flex items-center">
                            <Check className="h-3 w-3 mr-1" />
                            ACKNOWLEDGED
                          </span>
                        )}
                        {isAnalyzed && (
                          <span className="px-2 py-1 text-xs font-bold bg-purple-500 text-white rounded">
                            ANALYZED
                          </span>
                        )}
                        {hasTasksAdded && (
                          <span className="px-2 py-1 text-xs font-bold bg-blue-500 text-white rounded">
                            {thread.state?.tasks_added?.length} TASKS ADDED
                          </span>
                        )}
                        <span className="text-xs text-gray-500">
                          Score: {thread.priority_score}
                        </span>
                      </div>

                      {/* Sender */}
                      <div className="flex items-center space-x-2 mb-2">
                        <User className="h-4 w-4 text-gray-400" />
                        <span className="font-medium text-white">{name}</span>
                        <span className="text-sm text-gray-400">{email}</span>
                      </div>

                      {/* Subject */}
                      <h3 className="font-semibold text-white mb-2">
                        {thread.subject || '(No subject)'}
                      </h3>

                      {/* Preview */}
                      {!isExpanded && (
                        <p className="text-sm text-gray-300 line-clamp-2">
                          {thread.snippet}
                        </p>
                      )}
                    </div>

                    {/* Quick Actions */}
                    <div className="flex flex-col space-y-2">
                      {!isAcknowledged && (
                        <button
                          onClick={() => acknowledgeEmail(thread.id)}
                          className="px-3 py-2 bg-green-100 text-green-700 text-sm font-medium rounded-lg hover:bg-green-200 flex items-center space-x-1"
                        >
                          <Check className="h-4 w-4" />
                          <span>Acknowledge</span>
                        </button>
                      )}
                      
                      <button
                        onClick={() => analyzeThread(thread.id)}
                        disabled={analyzing}
                        className="px-3 py-2 bg-gradient-to-r from-red-600 to-orange-600 text-white text-sm font-medium rounded-lg hover:from-red-700 hover:to-orange-700 flex items-center space-x-1 shadow-md disabled:opacity-50"
                      >
                        <Brain className="h-4 w-4" />
                        <span>AI Analysis</span>
                      </button>

                      <button
                        onClick={() => setExpandedThread(isExpanded ? null : thread.id)}
                        className="p-2 bg-gray-700 border border-gray-600 rounded-lg hover:bg-gray-600"
                      >
                        {isExpanded ? <ChevronUp className="h-4 w-4 text-gray-300" /> : <ChevronDown className="h-4 w-4 text-gray-300" />}
                      </button>
                    </div>
                  </div>

                  {/* Smart AI Analysis */}
                  {isExpanded && analysis && (
                    <div className="mt-6 pt-6 border-t border-gray-700">
                      <div className="bg-gray-700 rounded-xl p-6 border border-gray-600">
                        <div className="flex items-center mb-4">
                          <div className="p-2 bg-red-600 rounded-lg mr-3">
                            <Brain className="h-5 w-5 text-white" />
                          </div>
                          <div>
                            <h4 className="font-bold text-white">AI Assistant Analysis</h4>
                            <p className="text-xs text-gray-300">Understanding context, not just keywords</p>
                          </div>
                        </div>

                        <div className="prose prose-sm max-w-none prose-invert">
                          <div className="text-gray-200 leading-relaxed">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {analysis.analysis || 'No analysis available'}
                            </ReactMarkdown>
                          </div>
                        </div>

                        {/* Debug: Log tasks to console */}
                        {console.log('Analysis tasks:', analysis.tasks)}

                        {/* Extracted Actions */}
                        {analysis.tasks && analysis.tasks.length > 0 && (
                          <div className="mt-6 pt-4 border-t border-gray-600">
                            <h5 className="text-sm font-bold text-white mb-3">Extracted Action Items:</h5>
                            <div className="space-y-2">
                              {analysis.tasks.map((task: any, idx: number) => (
                                <div key={idx} className="flex items-start space-x-2 bg-gray-600 rounded-lg p-3">
                                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm text-white">{task.action}</p>
                                    <div className="flex items-center space-x-3 mt-1 flex-wrap">
                                      {task.due_date && (
                                        <span className="text-xs text-gray-300">
                                          <Calendar className="h-3 w-3 inline mr-1" />
                                          Due: {task.due_date}
                                        </span>
                                      )}
                                      {task.time_estimate && (
                                        <span className="text-xs text-gray-300">
                                          <Clock className="h-3 w-3 inline mr-1" />
                                          ~{task.time_estimate}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex items-center space-x-1 flex-shrink-0">
                                    <button
                                      onClick={async () => {
                                        // Add to calendar
                                        try {
                                          let calendarDate = '';
                                          let calendarTime = '10:00 AM';

                                          if (task.due_date) {
                                            // Try to parse the due date
                                            const dueDate = new Date(task.due_date);
                                            if (!isNaN(dueDate.getTime())) {
                                              calendarDate = dueDate.toISOString().split('T')[0];
                                            }
                                          }

                                          if (!calendarDate) {
                                            const tomorrow = new Date();
                                            tomorrow.setDate(tomorrow.getDate() + 1);
                                            calendarDate = tomorrow.toISOString().split('T')[0];
                                          }

                                          const response = await fetch('/api/backend/calendar/create-event', {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({
                                              title: task.action,
                                              date: calendarDate,
                                              time: calendarTime,
                                              description: `From: ${thread.from}\nSubject: ${thread.subject}\n\nEstimate: ${task.time_estimate || 'N/A'}`,
                                              location: 'Chili\'s - Auburn Hills #605',
                                              reminder_days: 1
                                            })
                                          });

                                          const data = await response.json();
                                          if (data.success) {
                                            alert(`✅ Added to calendar!\n\n${task.action}\n${calendarDate} at ${calendarTime}`);
                                          } else {
                                            alert(`❌ Failed: ${data.error}`);
                                          }
                                        } catch (error) {
                                          alert('❌ Failed to add to calendar');
                                        }
                                      }}
                                      className="p-1 bg-blue-600 hover:bg-blue-700 text-white rounded"
                                      title="Add to Google Calendar"
                                    >
                                      <Calendar className="h-3 w-3" />
                                    </button>
                                    <button
                                      onClick={() => addSingleTask(task, thread.id)}
                                      className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded flex items-center space-x-1"
                                    >
                                      <Plus className="h-3 w-3" />
                                      <span>Add</span>
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>

                            <button
                              onClick={() => addAllTasks(analysis.tasks, thread.id)}
                              className="mt-4 w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg flex items-center justify-center space-x-2"
                            >
                              <Plus className="h-4 w-4" />
                              <span>Add All to Todo List</span>
                              <ArrowRight className="h-4 w-4" />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
