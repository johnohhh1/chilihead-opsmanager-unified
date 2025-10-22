'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin, Bell, X } from 'lucide-react';

interface CalendarModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  suggestedDate: string; // YYYY-MM-DD
  suggestedTime: string; // HH:MM AM/PM
  description?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  timeEstimate?: string;
  dueDate?: string;
}

export default function CalendarModal({
  isOpen,
  onClose,
  title,
  suggestedDate,
  suggestedTime,
  description = '',
  priority = 'medium',
  timeEstimate,
  dueDate
}: CalendarModalProps) {
  const [eventTitle, setEventTitle] = useState(title);
  const [date, setDate] = useState(suggestedDate);
  const [time, setTime] = useState(suggestedTime);
  const [location, setLocation] = useState("Chili's - Auburn Hills #605");
  const [reminderDays, setReminderDays] = useState(1);
  const [notes, setNotes] = useState(description);
  const [loading, setLoading] = useState(false);

  // Update when props change
  useEffect(() => {
    setEventTitle(title);
    setDate(suggestedDate);
    setTime(suggestedTime);
    setNotes(description);

    // Smart reminder based on priority and due date
    if (priority === 'urgent') {
      setReminderDays(0); // Same day reminder
    } else if (priority === 'high') {
      setReminderDays(1); // 1 day before
    } else if (priority === 'medium') {
      setReminderDays(2); // 2 days before
    } else {
      setReminderDays(3); // 3 days before
    }
  }, [title, suggestedDate, suggestedTime, description, priority]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/backend/calendar/create-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: eventTitle,
          date: date,
          time: time,
          description: notes,
          location: location,
          reminder_days: reminderDays
        })
      });

      const data = await response.json();

      if (data.success) {
        // Success feedback
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2';
        toast.innerHTML = `
          <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
          <span>Added to Google Calendar!</span>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);

        onClose();
      } else {
        alert(`❌ Failed to add to calendar:\n${data.error}`);
      }
    } catch (error) {
      console.error('Failed to add to calendar:', error);
      alert('❌ Failed to add to calendar. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // Smart date suggestions
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const nextWeek = new Date(today);
  nextWeek.setDate(nextWeek.getDate() + 7);

  const formatDateForInput = (date: Date) => date.toISOString().split('T')[0];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-800 rounded-lg shadow-2xl max-w-md w-full border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Calendar className="h-5 w-5 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Add to Calendar</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Smart suggestion banner */}
          {dueDate && (
            <div className="bg-blue-900/30 border border-blue-600/50 rounded-lg p-3 text-sm">
              <div className="flex items-start space-x-2">
                <Bell className="h-4 w-4 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-blue-300 font-medium">Smart Suggestion</p>
                  <p className="text-blue-400/80 text-xs mt-1">
                    Due date: {new Date(dueDate).toLocaleDateString()} -
                    Setting calendar event for the due date with {reminderDays} day reminder
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Event Title */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Event Title
            </label>
            <input
              type="text"
              value={eventTitle}
              onChange={(e) => setEventTitle(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              required
            />
          </div>

          {/* Date and Time */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Date
              </label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
                required
              />
              {/* Quick date buttons */}
              <div className="flex gap-1 mt-2">
                <button
                  type="button"
                  onClick={() => setDate(formatDateForInput(today))}
                  className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                >
                  Today
                </button>
                <button
                  type="button"
                  onClick={() => setDate(formatDateForInput(tomorrow))}
                  className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                >
                  Tomorrow
                </button>
                <button
                  type="button"
                  onClick={() => setDate(formatDateForInput(nextWeek))}
                  className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                >
                  Next Week
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Time
              </label>
              <select
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                <option value="8:00 AM">8:00 AM</option>
                <option value="9:00 AM">9:00 AM</option>
                <option value="10:00 AM">10:00 AM</option>
                <option value="11:00 AM">11:00 AM</option>
                <option value="12:00 PM">12:00 PM</option>
                <option value="1:00 PM">1:00 PM</option>
                <option value="2:00 PM">2:00 PM</option>
                <option value="3:00 PM">3:00 PM</option>
                <option value="4:00 PM">4:00 PM</option>
                <option value="5:00 PM">5:00 PM</option>
                <option value="6:00 PM">6:00 PM</option>
                <option value="7:00 PM">7:00 PM</option>
              </select>
            </div>
          </div>

          {/* Location */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
              <MapPin className="h-4 w-4 mr-1" />
              Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>

          {/* Reminder */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2 flex items-center">
              <Bell className="h-4 w-4 mr-1" />
              Email Reminder
            </label>
            <select
              value={reminderDays}
              onChange={(e) => setReminderDays(Number(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value={0}>Same day</option>
              <option value={1}>1 day before</option>
              <option value={2}>2 days before</option>
              <option value={3}>3 days before</option>
              <option value={5}>5 days before</option>
              <option value={7}>1 week before</option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="w-full bg-gray-900 border border-gray-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
              placeholder="Add any additional details..."
            />
            {timeEstimate && (
              <p className="text-xs text-gray-400 mt-1">
                Estimated time: {timeEstimate}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4" />
                  <span>Add to Calendar</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
