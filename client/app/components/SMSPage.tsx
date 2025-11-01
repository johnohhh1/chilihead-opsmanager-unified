'use client';

import React, { useState, useEffect } from 'react';

interface Manager {
  id: string;
  name: string;
  phone: string;
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

  useEffect(() => {
    loadManagers();
  }, []);

  const loadManagers = async () => {
    try {
      const res = await fetch('http://localhost:8002/api/sms/managers');
      const data = await res.json();
      setManagers(data.managers);
      // Select all managers by default
      setSelectedManagers(data.managers.map((m: Manager) => m.id));
    } catch (err) {
      setError('Failed to load managers');
      console.error(err);
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
      const res = await fetch('http://localhost:8002/api/sms/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: draftPrompt })
      });

      if (!res.ok) throw new Error('Failed to draft message');

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
      const res = await fetch('http://localhost:8002/api/sms/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          manager_ids: selectedManagers
        })
      });

      if (!res.ok) throw new Error('Failed to send message');

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
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Text Managers</h1>
        <p className="text-gray-600 mb-8">Send SMS messages to your management team</p>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Success Display */}
        {sendResults && sendResults.success && (
          <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded mb-6">
            ✅ Message sent successfully to {sendResults.total_sent} manager(s)!
          </div>
        )}

        {/* AI Draft Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">✨ AI Message Drafter</h2>
          <p className="text-sm text-gray-600 mb-4">
            Tell me what you want to communicate and I'll draft a professional message for you.
          </p>
          
          <div className="space-y-4">
            <textarea
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="Example: Need coverage for Friday dinner rush 5-9pm, bonus pay available"
              value={draftPrompt}
              onChange={(e) => setDraftPrompt(e.target.value)}
              disabled={isDrafting}
            />
            
            <button
              onClick={handleDraftMessage}
              disabled={isDrafting || !draftPrompt.trim()}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {isDrafting ? 'Drafting...' : '✨ Draft Message with AI'}
            </button>
          </div>
        </div>

        {/* Message Editor */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Message</h2>
            <span className="text-sm text-gray-500">
              {message.length} / 1600 characters
            </span>
          </div>
          
          <textarea
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={6}
            placeholder="Type or edit your message here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={1600}
          />
        </div>

        {/* Manager Selection */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Send To</h2>
            <div className="space-x-2">
              <button
                onClick={selectAll}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Select All
              </button>
              <span className="text-gray-300">|</span>
              <button
                onClick={selectNone}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Select None
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {managers.map((manager) => (
              <label
                key={manager.id}
                className="flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedManagers.includes(manager.id)}
                  onChange={() => toggleManager(manager.id)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex-1">
                  <div className="font-medium">{manager.name}</div>
                  <div className="text-sm text-gray-500">{manager.phone}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Send Button */}
        <button
          onClick={handleSendMessage}
          disabled={isSending || !message.trim() || selectedManagers.length === 0}
          className="w-full bg-blue-600 text-white px-6 py-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-lg font-semibold"
        >
          {isSending ? 'Sending...' : `📱 Send to ${selectedManagers.length} Manager(s)`}
        </button>

        {/* Send Results Details */}
        {sendResults && (
          <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold mb-3">Send Results</h3>
            <div className="space-y-2">
              {sendResults.results.map((result: any, idx: number) => (
                <div
                  key={idx}
                  className={`flex items-center space-x-2 text-sm ${
                    result.success ? 'text-green-700' : 'text-red-700'
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
