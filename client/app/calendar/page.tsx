'use client';

import { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin, RefreshCw } from 'lucide-react';

interface CalendarEvent {
  id: string;
  summary: string;
  description?: string;
  location?: string;
  start: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  htmlLink: string;
  status: string;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [daysAhead, setDaysAhead] = useState(30);

  const fetchEvents = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/backend/calendar/events?days_ahead=${daysAhead}`);
      const data = await response.json();

      if (data.success) {
        setEvents(data.events);
      } else {
        setError(data.error || 'Failed to fetch events');
      }
    } catch (err) {
      setError('Failed to fetch calendar events');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [daysAhead]);

  const formatEventDate = (event: CalendarEvent) => {
    const startDate = event.start.dateTime || event.start.date;
    if (!startDate) return 'No date';

    const date = new Date(startDate);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const isTomorrow = date.toDateString() === tomorrow.toDateString();

    let dateLabel = '';
    if (isToday) dateLabel = 'Today';
    else if (isTomorrow) dateLabel = 'Tomorrow';
    else dateLabel = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

    // Only show time if it's a dateTime (not all-day event)
    if (event.start.dateTime) {
      const time = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
      return `${dateLabel} at ${time}`;
    }

    return dateLabel;
  };

  const groupEventsByDate = () => {
    const grouped: { [key: string]: CalendarEvent[] } = {};

    events.forEach(event => {
      const startDate = event.start.dateTime || event.start.date;
      if (!startDate) return;

      const date = new Date(startDate);
      const dateKey = date.toDateString();

      if (!grouped[dateKey]) {
        grouped[dateKey] = [];
      }
      grouped[dateKey].push(event);
    });

    return grouped;
  };

  const groupedEvents = groupEventsByDate();
  const sortedDateKeys = Object.keys(groupedEvents).sort((a, b) =>
    new Date(a).getTime() - new Date(b).getTime()
  );

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Calendar className="h-8 w-8 text-red-500" />
          <div>
            <h1 className="text-2xl font-bold text-white">My Calendar</h1>
            <p className="text-gray-400 text-sm">Upcoming events and deadlines</p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Days filter */}
          <select
            value={daysAhead}
            onChange={(e) => setDaysAhead(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 text-white px-3 py-2 rounded text-sm"
          >
            <option value={7}>Next 7 days</option>
            <option value={14}>Next 2 weeks</option>
            <option value={30}>Next 30 days</option>
            <option value={60}>Next 60 days</option>
            <option value={90}>Next 90 days</option>
          </select>

          {/* Refresh button */}
          <button
            onClick={fetchEvents}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-900/30 border border-red-600 text-red-300 p-4 rounded mb-6">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-400">Loading events...</p>
        </div>
      )}

      {/* No events */}
      {!loading && events.length === 0 && !error && (
        <div className="text-center py-12 bg-gray-800/50 rounded-lg">
          <Calendar className="h-12 w-12 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400 text-lg">No upcoming events</p>
          <p className="text-gray-500 text-sm mt-2">Events you create will appear here</p>
        </div>
      )}

      {/* Events grouped by date */}
      {!loading && events.length > 0 && (
        <div className="space-y-6">
          {sortedDateKeys.map(dateKey => {
            const date = new Date(dateKey);
            const now = new Date();
            const isToday = date.toDateString() === now.toDateString();
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);
            const isTomorrow = date.toDateString() === tomorrow.toDateString();

            let dateLabel = '';
            if (isToday) dateLabel = 'Today';
            else if (isTomorrow) dateLabel = 'Tomorrow';
            else dateLabel = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

            return (
              <div key={dateKey}>
                {/* Date header */}
                <h2 className="text-lg font-semibold text-white mb-3 flex items-center">
                  <div className={`w-1 h-6 ${isToday ? 'bg-red-500' : 'bg-gray-600'} mr-3`} />
                  {dateLabel}
                  <span className="text-gray-500 text-sm ml-2">
                    ({groupedEvents[dateKey].length} {groupedEvents[dateKey].length === 1 ? 'event' : 'events'})
                  </span>
                </h2>

                {/* Events for this date */}
                <div className="space-y-3 ml-4">
                  {groupedEvents[dateKey].map(event => (
                    <a
                      key={event.id}
                      href={event.htmlLink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block bg-gray-800/70 hover:bg-gray-800 border border-gray-700 rounded-lg p-4 transition-colors"
                    >
                      {/* Event title */}
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-white font-medium flex-1">{event.summary}</h3>
                        <span className={`text-xs px-2 py-1 rounded ${
                          event.status === 'confirmed'
                            ? 'bg-green-900/30 text-green-400'
                            : 'bg-gray-700 text-gray-400'
                        }`}>
                          {event.status}
                        </span>
                      </div>

                      {/* Event time */}
                      {event.start.dateTime && (
                        <div className="flex items-center text-gray-400 text-sm mb-2">
                          <Clock className="h-4 w-4 mr-2" />
                          <span>
                            {new Date(event.start.dateTime).toLocaleTimeString('en-US', {
                              hour: 'numeric',
                              minute: '2-digit'
                            })}
                            {event.end.dateTime && (
                              <> - {new Date(event.end.dateTime).toLocaleTimeString('en-US', {
                                hour: 'numeric',
                                minute: '2-digit'
                              })}</>
                            )}
                          </span>
                        </div>
                      )}

                      {/* Event location */}
                      {event.location && (
                        <div className="flex items-center text-gray-400 text-sm mb-2">
                          <MapPin className="h-4 w-4 mr-2" />
                          <span>{event.location}</span>
                        </div>
                      )}

                      {/* Event description */}
                      {event.description && (
                        <p className="text-gray-500 text-sm mt-2 line-clamp-2">
                          {event.description}
                        </p>
                      )}
                    </a>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
