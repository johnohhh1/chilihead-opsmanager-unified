'use client';

import React, { useState, useEffect } from 'react';

interface Manager {
  id: string;
  name: string;
  phone: string;
  twilio_configured?: boolean;
}

interface TwilioStatus {
  configured: boolean;
  from_number: string | null;
  manager_count: number;
}

export default function SMSPage() {
  const [managers, setManagers] = useState<Manager[]>([]);
  const [selectedManagers, setSelectedManagers] = useState<string[]>([]);
  const [message, setMessage] = useState('');
  const [draftPrompt, setDraftPrompt] = useState('');
  const [isDrafting, setIsDrafting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sendResults, setSendResults] = useState<any>(null);
  const [error, setError] = useState('');
  const [twilioStatus, setTwilioStatus] = useState<TwilioStatus | null>(null);

  useEffect(() => {
    loadManagers();
    loadTwilioStatus();
  }, []);

  const loadManagers = async () => {
    try {
      const res = await fetch('/api/backend/api/sms/managers');
      const data = await res.json();
      setManagers(data.managers || []);
      // Select all managers by default
      setSelectedManagers((data.managers || []).map((m: Manager) => m.id));
    } catch (err) {
      setError('Failed to load managers. Is the backend running?');
      console.error(err);
    }
  };

  const loadTwilioStatus = async () => {
    try {
      const res = await fetch('/api/backend/api/sms/status');
      const data = await res.json();
      setTwilioStatus(data);
    } catch (err) {
      console.error('Failed to load Twilio status:', err);
    }
  };

  const handleDraftMessage = async () => {
    if (!draftPrompt.trim()) {
      setError('Please enter what you want to communicate');
      return;
    }

    setIsDrafting(true);
    setError('');

    try {
      const res = await fetch('/api/backend/api/sms/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: draftPrompt })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Failed to draft message' }));
        throw new Error(errorData.detail || 'Failed to draft message');
      }

      const data = await res.json();
      setMessage(data.drafted_message);
      setDraftPrompt(''); // Clear the prompt after drafting
    } catch (err: any) {
      setError(err.message || 'Failed to draft message');
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }

    if (selectedManagers.length === 0) {
      setError('Please select at least one manager');
      return;
    }

    setIsSending(true);
    setError('');
    setSendResults(null);

    try {
      const res = await fetch('/api/backend/api/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          manager_ids: selectedManagers
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Failed to send message' }));
        throw new Error(errorData.detail || 'Failed to send message');
      }

      const data = await res.json();
      setSendResults(data);

      if (data.success) {
        // Clear message after successful send
        setMessage('');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const toggleManager = (managerId: string) => {
    setSelectedManagers(prev =>
      prev.includes(managerId)
        ? prev.filter(id => id !== managerId)
        : [...prev, managerId]
    );
  };

  const selectAll = () => {
    setSelectedManagers(managers.map(m => m.id));
  };

  const selectNone = () => {
    setSelectedManagers([]);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2 text-white">📱 Text Managers</h1>
        <p className="text-gray-400 mb-4">Send SMS messages to your management team</p>

        {/* Twilio Status */}
        {twilioStatus && !twilioStatus.configured && (
          <div className="bg-yellow-900/30 border border-yellow-700 text-yellow-300 px-4 py-3 rounded mb-6">
            <div className="font-semibold mb-2">⚠️ Twilio Not Configured</div>
            <p className="text-sm">
              To enable SMS, add these to your server/.env file:
            </p>
            <code className="block bg-gray-900 p-2 mt-2 rounded text-xs text-green-400">
              TWILIO_ACCOUNT_SID=your_sid<br/>
              TWILIO_AUTH_TOKEN=your_token<br/>
              TWILIO_PHONE_NUMBER=+1234567890
            </code>
          </div>
        )}

        {twilioStatus && twilioStatus.configured && (
          <div className="bg-green-900/30 border border-green-700 text-green-300 px-4 py-3 rounded mb-6">
            ✅ Twilio configured - sending from {twilioStatus.from_number}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/30 border border-red-700 text-red-300 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Success Display */}
        {sendResults && sendResults.success && (
          <div className="bg-green-900/30 border border-green-700 text-green-300 px-4 py-3 rounded mb-6">
            ✅ Message sent successfully to {sendResults.total_sent} manager(s)!
          </div>
        )}

        {sendResults && !sendResults.success && sendResults.total_failed > 0 && (
          <div className="bg-orange-900/30 border border-orange-700 text-orange-300 px-4 py-3 rounded mb-6">
            ⚠️ Sent to {sendResults.total_sent}, failed to send to {sendResults.total_failed} manager(s)
          </div>
        )}

        {/* AI Draft Section */}
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-white">✨ AI Message Drafter</h2>
          <p className="text-sm text-gray-400 mb-4">
            Tell me what you want to communicate and I'll draft a professional message for you.
          </p>

          <div className="space-y-4">
            <textarea
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-gray-400"
              rows={3}
              placeholder="Example: Need coverage for Friday dinner rush 5-9pm, bonus pay available"
              value={draftPrompt}
              onChange={(e) => setDraftPrompt(e.target.value)}
              disabled={isDrafting}
            />

            <button
              onClick={handleDraftMessage}
              disabled={isDrafting || !draftPrompt.trim()}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
            >
              {isDrafting ? 'Drafting...' : '✨ Draft Message with AI'}
            </button>
          </div>
        </div>

        {/* Message Editor */}
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Message</h2>
            <span className="text-sm text-gray-400">
              {message.length} / 1600 characters
            </span>
          </div>

          <textarea
            className="w-full px-4 py-3 bg-gray-700 border border-gray-600 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 placeholder-gray-400"
            rows={6}
            placeholder="Type or edit your message here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={1600}
          />
        </div>

        {/* Manager Selection */}
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Send To</h2>
            <div className="space-x-2">
              <button
                onClick={selectAll}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Select All
              </button>
              <span className="text-gray-600">|</span>
              <button
                onClick={selectNone}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Select None
              </button>
            </div>
          </div>

          {managers.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              No managers found. Check backend connection.
            </div>
          ) : (
            <div className="space-y-2">
              {managers.map((manager) => (
                <label
                  key={manager.id}
                  className="flex items-center space-x-3 p-3 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedManagers.includes(manager.id)}
                    onChange={() => toggleManager(manager.id)}
                    className="w-5 h-5 text-red-600 rounded focus:ring-2 focus:ring-red-500"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-white">{manager.name}</div>
                    <div className="text-sm text-gray-400">{manager.phone}</div>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Send Button */}
        <button
          onClick={handleSendMessage}
          disabled={isSending || !message.trim() || selectedManagers.length === 0 || (twilioStatus && !twilioStatus.configured)}
          className="w-full bg-red-600 text-white px-6 py-4 rounded-lg hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors text-lg font-semibold"
        >
          {isSending ? 'Sending...' : `📱 Send to ${selectedManagers.length} Manager(s)`}
        </button>

        {twilioStatus && !twilioStatus.configured && (
          <p className="text-center text-yellow-400 text-sm mt-2">
            Configure Twilio credentials to send messages
          </p>
        )}

        {/* Send Results Details */}
        {sendResults && sendResults.results && sendResults.results.length > 0 && (
          <div className="mt-6 bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
            <h3 className="font-semibold mb-3 text-white">Send Results</h3>
            <div className="space-y-2">
              {sendResults.results.map((result: any, idx: number) => (
                <div
                  key={idx}
                  className={`flex items-center space-x-2 text-sm ${
                    result.success ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  <span>{result.success ? '✅' : '❌'}</span>
                  <span className="font-medium">{result.manager_name}:</span>
                  <span>{result.success ? 'Sent' : result.error}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
