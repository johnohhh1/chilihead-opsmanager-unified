'use client';

import { useState, useEffect } from 'react';
import { CheckCircle2, Circle, Clock, RefreshCw, Plus } from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description?: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  due_date?: string;
  assigned_to?: string;
  status: 'todo' | 'in_progress' | 'completed';
  created_at: string;
  updated_at: string;
  pushed_by: string;
}

interface TeamBoardPageProps {
  onNavigate?: (page: 'triage' | 'todo' | 'delegations' | 'team-board') => void;
}

export default function TeamBoardPage({ onNavigate }: TeamBoardPageProps = {}) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'completed'>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    priority: 'normal' as Task['priority'],
    due_date: '',
    assigned_to: ''
  });

  const TEAM_BOARD_URL = process.env.NEXT_PUBLIC_TEAM_BOARD_URL || 'https://chilihead-team-board.vercel.app';

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${TEAM_BOARD_URL}/api/tasks`);
      const data = await response.json();
      if (data.success) {
        setTasks(data.tasks);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchTasks, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleTaskStatus = async (taskId: string, currentStatus: Task['status']) => {
    const newStatus = currentStatus === 'completed' ? 'todo' :
                      currentStatus === 'todo' ? 'in_progress' : 'completed';

    try {
      const response = await fetch(`${TEAM_BOARD_URL}/api/tasks?id=${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'team-member-access'
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        fetchTasks();
      } else {
        console.error('Failed to update task status:', await response.text());
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const addNewTask = async () => {
    if (!newTask.title.trim()) return;

    try {
      const response = await fetch(`${TEAM_BOARD_URL}/api/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'team-member-access'
        },
        body: JSON.stringify({
          title: newTask.title,
          description: newTask.description,
          priority: newTask.priority,
          due_date: newTask.due_date || undefined,
          assigned_to: newTask.assigned_to,
          status: 'todo',
          pushed_by: 'Manager (OpsManager)'
        })
      });

      if (response.ok) {
        setNewTask({
          title: '',
          description: '',
          priority: 'normal',
          due_date: '',
          assigned_to: ''
        });
        setShowAddForm(false);
        fetchTasks();
      }
    } catch (error) {
      console.error('Failed to add task:', error);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'normal': return 'bg-blue-500';
      case 'low': return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <RefreshCw className="h-5 w-5 text-blue-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const filteredTasks = tasks.filter(task => {
    if (filter === 'all') return true;
    return task.status === filter;
  });

  const todoCount = tasks.filter(t => t.status === 'todo').length;
  const inProgressCount = tasks.filter(t => t.status === 'in_progress').length;
  const completedCount = tasks.filter(t => t.status === 'completed').length;

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
              className="px-4 py-2 rounded-lg font-medium text-sm bg-red-500 text-white"
            >
              👥 Team Board
            </button>
          </nav>
        </div>
      )}

      {/* Header */}
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-3xl font-bold text-white">👥 Team Board (Mirror)</h1>
            <span className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-full">
              Live Sync
            </span>
          </div>
          <button
            onClick={fetchTasks}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            title="Refresh tasks"
          >
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Stats */}
        <div className="flex items-center space-x-6 mt-4 text-sm">
          <div className="flex items-center space-x-2">
            <Circle className="h-4 w-4 text-gray-400" />
            <span className="text-gray-300">{todoCount} To Do</span>
          </div>
          <div className="flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 text-blue-500" />
            <span className="text-gray-300">{inProgressCount} In Progress</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-gray-300">{completedCount} Completed</span>
          </div>
        </div>
      </div>

      {/* Add Task Form */}
      <div className="mb-6 bg-gray-800 rounded-xl border border-gray-700 p-6">
        {!showAddForm ? (
          <button
            onClick={() => setShowAddForm(true)}
            className="w-full flex items-center justify-center space-x-2 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
          >
            <Plus className="h-5 w-5" />
            <span>Add New Task</span>
          </button>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-white">Add New Task</h3>
              <button
                onClick={() => setShowAddForm(false)}
                className="text-gray-400 hover:text-white"
              >
                Cancel
              </button>
            </div>

            <input
              type="text"
              placeholder="Task title *"
              value={newTask.title}
              onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />

            <textarea
              placeholder="Description (optional)"
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              rows={3}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Priority</label>
                <select
                  value={newTask.priority}
                  onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as Task['priority'] })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 focus:border-red-500"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Due Date</label>
                <input
                  type="date"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Assigned To</label>
                <input
                  type="text"
                  placeholder="Name"
                  value={newTask.assigned_to}
                  onChange={(e) => setNewTask({ ...newTask, assigned_to: e.target.value })}
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-red-500 focus:border-red-500"
                />
              </div>
            </div>

            <button
              onClick={addNewTask}
              disabled={!newTask.title.trim()}
              className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              Add Task
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="mb-6 flex items-center space-x-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'all' ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          All Tasks
        </button>
        <button
          onClick={() => setFilter('todo')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'todo' ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          To Do
        </button>
        <button
          onClick={() => setFilter('in_progress')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'in_progress' ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          In Progress
        </button>
        <button
          onClick={() => setFilter('completed')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'completed' ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          Completed
        </button>
      </div>

      {/* Tasks */}
      {loading ? (
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
          <p className="text-gray-400">Loading tasks...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-gray-800 rounded-xl border border-gray-700">
          <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
          <p className="text-lg font-medium text-white">
            {filter === 'all' ? 'No tasks yet' : `No ${filter.replace('_', ' ')} tasks`}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Add tasks here or push from your Personal Todo
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTasks.map((task) => {
            const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'completed';

            return (
              <div
                key={task.id}
                className={`bg-gray-800 border rounded-xl p-6 transition-all hover:shadow-lg ${
                  task.status === 'completed'
                    ? 'border-gray-700 opacity-60'
                    : isOverdue
                    ? 'border-red-600'
                    : 'border-gray-700'
                }`}
              >
                <div className="flex items-start space-x-4">
                  {/* Status Icon (clickable) */}
                  <button
                    onClick={() => toggleTaskStatus(task.id, task.status)}
                    className="flex-shrink-0 mt-1 hover:scale-110 transition-transform"
                    title={`Mark as ${task.status === 'completed' ? 'todo' : task.status === 'todo' ? 'in progress' : 'completed'}`}
                  >
                    {getStatusIcon(task.status)}
                  </button>

                  {/* Task Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className={`text-lg font-medium text-white ${task.status === 'completed' ? 'line-through' : ''}`}>
                        {task.title}
                      </h3>
                      <div className={`ml-4 h-2 w-2 rounded-full flex-shrink-0 ${getPriorityColor(task.priority)}`} title={task.priority} />
                    </div>

                    {task.description && (
                      <p className="text-gray-400 text-sm mb-3 whitespace-pre-wrap">{task.description}</p>
                    )}

                    <div className="flex items-center space-x-4 text-sm text-gray-400">
                      {task.due_date && (
                        <div className="flex items-center space-x-1">
                          <Clock className="h-4 w-4" />
                          <span className={isOverdue ? 'text-red-500 font-medium' : ''}>
                            {formatDate(task.due_date)}
                          </span>
                        </div>
                      )}
                      {task.assigned_to && (
                        <span className="px-2 py-1 bg-gray-700 rounded text-xs">
                          👤 {task.assigned_to}
                        </span>
                      )}
                      <span className="text-xs">
                        Pushed by {task.pushed_by}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
