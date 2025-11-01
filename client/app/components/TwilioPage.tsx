'use client';

import { useState, useEffect } from 'react';
import { Phone, MessageSquare, RefreshCw, CheckCircle, AlertCircle, Users } from 'lucide-react';

interface Manager {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  active_delegations: number;
}

interface TwilioStatus {
  enabled: boolean;
  configured: boolean;
  phone_number: string | null;
  message: string;
}

interface TwilioPageProps {
  onNavigate?: (page: 'triage' | 'todo' | 'delegations' | 'team-board' | 'sms') => void;
}

export default function TwilioPage({ onNavigate }: TwilioPageProps = {}) {
  const [managers, setManagers] = useState<Manager[]>([]);
  const [twilioStatus, setTwilioStatus] = useState<TwilioStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedManager, setSelectedManager] = useState<Manager | null>(null);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null);
  const [editingPhone, setEditingPhone] = useState<{ managerId: string; phone: string } | null>(null);

  useEffect(() => {
    fetchManagers();
    fetchTwilioStatus();
  }, []);

  const fetchManagers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/backend/sms/managers');
      const data = await response.json();
      if (data.success) {
        setManagers(data.managers);
      }
    } catch (error) {
      console.error('Failed to fetch managers:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTwilioStatus = async () => {
    try {
      const response = await fetch('/api/backend/sms/status');
      const data = await response.json();
      setTwilioStatus(data);
    } catch (error) {
      console.error('Failed to fetch Twilio status:', error);
    }
  };

  const updateManagerPhone = async (managerId: string, phone: string) => {
    try {
      // Find the delegation to update
      const response = await fetch(`/api/backend/delegations/${managerId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assignedToPhone: phone })
      });

      if (response.ok) {
        // Refresh managers list
        fetchManagers();
        setEditingPhone(null);

        // Show success notification
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Phone number updated';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
      }
    } catch (error) {
      console.error('Failed to update phone:', error);
    }
  };

  const sendSMS = async () => {
    if (!selectedManager || !message.trim() || !selectedManager.phone) {
      return;
    }

    setSending(true);
    setSendResult(null);

    try {
      const response = await fetch('/api/backend/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          manager_id: selectedManager.id,
          message: message.trim(),
          phone_number: selectedManager.phone
        })
      });

      const data = await response.json();

      if (data.success) {
        setSendResult({ success: true, message: 'SMS sent successfully!' });
        setMessage('');
        setTimeout(() => setSendResult(null), 5000);
      } else {
        setSendResult({ success: false, message: data.message || 'Failed to send SMS' });
      }
    } catch (error: any) {
      setSendResult({ success: false, message: error.message || 'Failed to send SMS' });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation Tabs */}
      {onNavigate && (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-3 mb-6">
          <nav className="flex space-x-2">
            <button
              onClick={() => onNavigate('triage')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              📧 Email Triage
            </button>
            <button
              onClick={() => onNavigate('todo')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              ✓ Personal Todo
            </button>
            <button
              onClick={() => onNavigate('delegations')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              🌶️ Delegations
            </button>
            <button
              onClick={() => onNavigate('team-board')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              👥 Team Board
            </button>
            <button
              className="px-4 py-2 rounded-lg font-medium text-sm bg-red-500 text-white"
            >
              📱 Text Managers
            </button>
          </nav>
        </div>
      )}

      {/* Header */}
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-red-600 rounded-lg">
              <Phone className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">📱 Manager SMS</h1>
              <p className="text-gray-400 mt-1">Send text messages to your team</p>
            </div>
          </div>
          <button
            onClick={fetchManagers}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Refresh managers"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Twilio Status */}
        {twilioStatus && (
          <div className={`mt-4 p-3 rounded-lg ${
            twilioStatus.enabled
              ? 'bg-green-900/30 border border-green-700'
              : 'bg-yellow-900/30 border border-yellow-700'
          }`}>
            <div className="flex items-center space-x-2">
              {twilioStatus.enabled ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <AlertCircle className="h-5 w-5 text-yellow-500" />
              )}
              <span className={twilioStatus.enabled ? 'text-green-300' : 'text-yellow-300'}>
                {twilioStatus.message}
              </span>
              {twilioStatus.enabled && twilioStatus.phone_number && (
                <span className="text-gray-400 ml-2">
                  From: {twilioStatus.phone_number}
                </span>
              )}
            </div>
          </div>
        )}

        {!twilioStatus?.enabled && (
          <div className="mt-4 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
            <h3 className="font-medium text-blue-300 mb-2">Twilio Setup Required</h3>
            <p className="text-sm text-gray-300 mb-2">
              To enable SMS, add these to your server/.env file:
            </p>
            <code className="block bg-gray-900 p-2 rounded text-xs text-green-400">
              TWILIO_ACCOUNT_SID=your_account_sid<br/>
              TWILIO_AUTH_TOKEN=your_auth_token<br/>
              TWILIO_PHONE_NUMBER=+1234567890
            </code>
            <p className="text-xs text-gray-400 mt-2">
              Install: pip install twilio
            </p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Managers List */}
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white flex items-center">
              <Users className="h-5 w-5 mr-2 text-red-500" />
              Managers ({managers.length})
            </h2>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-400">Loading managers...</p>
            </div>
          ) : managers.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No managers found</p>
              <p className="text-sm text-gray-500 mt-2">
                Create delegations to add managers
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {managers.map((manager) => (
                <div
                  key={manager.id}
                  className={`p-4 rounded-lg border transition-all cursor-pointer ${
                    selectedManager?.id === manager.id
                      ? 'bg-red-900/20 border-red-600'
                      : 'bg-gray-700 border-gray-600 hover:border-gray-500'
                  }`}
                  onClick={() => setSelectedManager(manager)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium text-white">{manager.name}</h3>

                      {editingPhone?.managerId === manager.id ? (
                        <div className="mt-2 flex items-center space-x-2">
                          <input
                            type="tel"
                            value={editingPhone.phone}
                            onChange={(e) => setEditingPhone({ ...editingPhone, phone: e.target.value })}
                            placeholder="+1234567890"
                            className="flex-1 px-3 py-1 bg-gray-600 border border-gray-500 rounded text-sm text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-red-500"
                            autoFocus
                          />
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              updateManagerPhone(manager.id, editingPhone.phone);
                            }}
                            className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded"
                          >
                            Save
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingPhone(null);
                            }}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="mt-1 flex items-center space-x-2">
                          {manager.phone ? (
                            <>
                              <Phone className="h-4 w-4 text-green-500" />
                              <span className="text-sm text-gray-300">{manager.phone}</span>
                            </>
                          ) : (
                            <>
                              <AlertCircle className="h-4 w-4 text-yellow-500" />
                              <span className="text-sm text-gray-400">No phone number</span>
                            </>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingPhone({ managerId: manager.id, phone: manager.phone || '' });
                            }}
                            className="text-xs text-blue-400 hover:text-blue-300"
                          >
                            {manager.phone ? 'Edit' : 'Add'}
                          </button>
                        </div>
                      )}

                      <div className="mt-2 flex items-center space-x-3 text-xs text-gray-400">
                        {manager.email && (
                          <span>📧 {manager.email}</span>
                        )}
                        <span className="px-2 py-1 bg-gray-600 rounded">
                          {manager.active_delegations} active
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Message Composer */}
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6">
          <h2 className="text-xl font-bold text-white flex items-center mb-4">
            <MessageSquare className="h-5 w-5 mr-2 text-red-500" />
            Compose Message
          </h2>

          {!selectedManager ? (
            <div className="text-center py-12">
              <MessageSquare className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Select a manager to send SMS</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Selected Manager */}
              <div className="p-4 bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Sending to:</p>
                    <p className="font-medium text-white">{selectedManager.name}</p>
                    {selectedManager.phone ? (
                      <p className="text-sm text-green-400 flex items-center mt-1">
                        <Phone className="h-4 w-4 mr-1" />
                        {selectedManager.phone}
                      </p>
                    ) : (
                      <p className="text-sm text-yellow-400 flex items-center mt-1">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        No phone number - add one first
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedManager(null)}
                    className="text-sm text-gray-400 hover:text-white"
                  >
                    Change
                  </button>
                </div>
              </div>

              {/* Message Input */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">Message</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message here..."
                  rows={6}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  disabled={!twilioStatus?.enabled || !selectedManager.phone}
                />
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-400">
                    {message.length} characters
                  </span>
                  <span className="text-xs text-gray-400">
                    ~{Math.ceil(message.length / 160)} SMS segment{Math.ceil(message.length / 160) !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Send Result */}
              {sendResult && (
                <div className={`p-3 rounded-lg ${
                  sendResult.success
                    ? 'bg-green-900/30 border border-green-700'
                    : 'bg-red-900/30 border border-red-700'
                }`}>
                  <div className="flex items-center space-x-2">
                    {sendResult.success ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                    <span className={sendResult.success ? 'text-green-300' : 'text-red-300'}>
                      {sendResult.message}
                    </span>
                  </div>
                </div>
              )}

              {/* Send Button */}
              <button
                onClick={sendSMS}
                disabled={!message.trim() || sending || !twilioStatus?.enabled || !selectedManager.phone}
                className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors flex items-center justify-center space-x-2"
              >
                {sending ? (
                  <>
                    <RefreshCw className="h-5 w-5 animate-spin" />
                    <span>Sending...</span>
                  </>
                ) : (
                  <>
                    <MessageSquare className="h-5 w-5" />
                    <span>Send SMS</span>
                  </>
                )}
              </button>

              {!twilioStatus?.enabled && (
                <p className="text-xs text-center text-yellow-400">
                  Twilio must be configured to send messages
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
