'use client';

import { useState, useEffect } from 'react';
import {
  CheckCircle2, Circle, Clock, AlertTriangle,
  Calendar, Trash2, RefreshCw, Filter, X, Plus, Edit2, Save, CheckSquare, Users
} from 'lucide-react';
import CalendarModal from './CalendarModal';

interface TodoItem {
  id: string;
  action: string;
  due_date?: string;
  time_estimate?: string;
  priority: string;
  completed: boolean;
  thread_id?: string;
  created_at: string;
  completed_at?: string;
  category?: 'urgent-important' | 'important-not-urgent' | 'urgent-not-important' | 'neither';
  google_task_id?: string;
}

interface TodoPageProps {
  onNavigate?: (page: 'triage' | 'todo' | 'delegations') => void;
}

export default function TodoPage({ onNavigate }: TodoPageProps = {}) {
  const [tasks, setTasks] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'active' | 'completed'>('active');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [newTaskText, setNewTaskText] = useState('');
  const [newTaskPriority, setNewTaskPriority] = useState('normal');
  const [newTaskDueDate, setNewTaskDueDate] = useState('');
  const [addingTask, setAddingTask] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState('');
  const [calendarModalOpen, setCalendarModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TodoItem | null>(null);
  const [syncingTaskId, setSyncingTaskId] = useState<string | null>(null);
  const [pushingTaskId, setPushingTaskId] = useState<string | null>(null);
  const [syncingFromTeam, setSyncingFromTeam] = useState(false);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/backend/state/tasks');
      const data = await response.json();
      console.log('Fetched tasks:', data);
      setTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const toggleTask = async (taskId: string) => {
    try {
      const response = await fetch('/api/backend/state/tasks/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(prev => prev.map(t =>
          t.id === taskId ? data.task : t
        ));
      }
    } catch (error) {
      console.error('Failed to toggle task:', error);
    }
  };

  const openCalendarModal = (task: TodoItem) => {
    setSelectedTask(task);
    setCalendarModalOpen(true);
  };

  const getSuggestedDateTime = (task: TodoItem) => {
    let suggestedDate = '';
    let suggestedTime = '10:00 AM';

    if (task.due_date) {
      const dueDate = new Date(task.due_date);
      suggestedDate = dueDate.toISOString().split('T')[0];

      // Smart time based on priority
      if (task.priority === 'urgent') {
        suggestedTime = '8:00 AM'; // Start of day for urgent
      } else if (task.priority === 'high') {
        suggestedTime = '9:00 AM';
      } else {
        suggestedTime = '10:00 AM';
      }
    } else {
      // No due date - suggest based on priority
      const baseDate = new Date();

      if (task.priority === 'urgent') {
        // Today
        suggestedDate = baseDate.toISOString().split('T')[0];
        suggestedTime = '8:00 AM';
      } else if (task.priority === 'high') {
        // Tomorrow
        baseDate.setDate(baseDate.getDate() + 1);
        suggestedDate = baseDate.toISOString().split('T')[0];
        suggestedTime = '9:00 AM';
      } else {
        // Next few days
        baseDate.setDate(baseDate.getDate() + 2);
        suggestedDate = baseDate.toISOString().split('T')[0];
        suggestedTime = '10:00 AM';
      }
    }

    return { suggestedDate, suggestedTime };
  };

  const deleteTask = async (taskId: string) => {
    try {
      const response = await fetch('/api/backend/state/tasks/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId })
      });

      if (response.ok) {
        // Remove task from state directly
        setTasks(prev => prev.filter(t => t.id !== taskId));

        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Task deleted';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      }
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const updateCategory = async (taskId: string, category: TodoItem['category']) => {
    try {
      const response = await fetch('/api/backend/state/tasks/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          updates: { category }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(prev => prev.map(t =>
          t.id === taskId ? data.task : t
        ));
      }
    } catch (error) {
      console.error('Failed to update category:', error);
    }
  };

  const addNewTask = async () => {
    if (!newTaskText.trim()) return;

    setAddingTask(true);
    try {
      const response = await fetch('/api/backend/state/tasks/add-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tasks: [{
            action: newTaskText,
            priority: newTaskPriority,
            due_date: newTaskDueDate || undefined
          }]
        })
      });

      if (response.ok) {
        setNewTaskText('');
        setNewTaskPriority('normal');
        setNewTaskDueDate('');
        await fetchTasks(); // Refresh task list

        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Task added';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      }
    } catch (error) {
      console.error('Failed to add task:', error);
    } finally {
      setAddingTask(false);
    }
  };

  const startEditing = (task: TodoItem) => {
    setEditingTaskId(task.id);
    setEditingText(task.action);
  };

  const saveEdit = async (taskId: string) => {
    if (!editingText.trim()) return;

    try {
      const response = await fetch('/api/backend/state/tasks/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          updates: { action: editingText }
        })
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(prev => prev.map(t =>
          t.id === taskId ? data.task : t
        ));
        setEditingTaskId(null);
        setEditingText('');

        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Task updated';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const cancelEdit = () => {
    setEditingTaskId(null);
    setEditingText('');
  };

  const syncToGoogleTasks = async (taskId: string) => {
    setSyncingTaskId(taskId);
    try {
      const response = await fetch(`/api/backend/state/tasks/${taskId}/sync-to-google-tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Update task in state with google_task_id
        setTasks(prev => prev.map(t =>
          t.id === taskId ? { ...t, google_task_id: data.google_task_id } : t
        ));

        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Task synced to Google Tasks';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      } else {
        // Handle error
        const errorMsg = data.error || 'Failed to sync task';
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = `✗ ${errorMsg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
      }
    } catch (error) {
      console.error('Failed to sync task to Google Tasks:', error);
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
      toast.textContent = '✗ Failed to sync task';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    } finally {
      setSyncingTaskId(null);
    }
  };

  const pushToTeamBoard = async (taskId: string) => {
    setPushingTaskId(taskId);
    try {
      const response = await fetch(`/api/backend/state/tasks/${taskId}/push-to-team`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = '✓ Task pushed to team board';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
      } else {
        // Handle error
        const errorMsg = data.error || 'Failed to push task';
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = `✗ ${errorMsg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
      }
    } catch (error) {
      console.error('Failed to push task to team board:', error);
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
      toast.textContent = '✗ Failed to push task';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    } finally {
      setPushingTaskId(null);
    }
  };

  const syncFromTeamBoard = async () => {
    setSyncingFromTeam(true);
    try {
      const response = await fetch('/api/backend/state/tasks/sync-from-team', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Refresh tasks to show updated status
        await fetchTasks();

        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = `✓ Synced ${data.updated_count} task update(s)`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
      } else {
        const errorMsg = data.error || 'Failed to sync from team board';
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = `✗ ${errorMsg}`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
      }
    } catch (error) {
      console.error('Failed to sync from team board:', error);
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
      toast.textContent = '✗ Failed to sync from team';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    } finally {
      setSyncingFromTeam(false);
    }
  };

  const autoCategory = (task: TodoItem): TodoItem['category'] => {
    if (task.category) return task.category;
    
    const isUrgent = task.priority === 'urgent' || 
                     (task.due_date && new Date(task.due_date) < new Date(Date.now() + 86400000 * 2));
    const isImportant = task.priority === 'urgent' || task.priority === 'high';
    
    if (isUrgent && isImportant) return 'urgent-important';
    if (!isUrgent && isImportant) return 'important-not-urgent';
    if (isUrgent && !isImportant) return 'urgent-not-important';
    return 'neither';
  };

  const getCategoryInfo = (category: TodoItem['category']) => {
    switch(category) {
      case 'urgent-important':
        return { label: 'Urgent & Important', color: 'bg-red-100 text-red-700', icon: '🔴' };
      case 'important-not-urgent':
        return { label: 'Important', color: 'bg-orange-100 text-orange-700', icon: '🟠' };
      case 'urgent-not-important':
        return { label: 'Urgent', color: 'bg-yellow-100 text-yellow-700', icon: '🟡' };
      case 'neither':
        return { label: 'Low Priority', color: 'bg-gray-100 text-gray-700', icon: '⚪' };
      default:
        return { label: 'Normal', color: 'bg-blue-100 text-blue-700', icon: '🔵' };
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

  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    // Filter by completion status
    if (filter === 'active' && task.completed) return false;
    if (filter === 'completed' && !task.completed) return false;
    
    // Filter by category
    if (categoryFilter !== 'all') {
      const taskCategory = autoCategory(task);
      if (taskCategory !== categoryFilter) return false;
    }
    
    return true;
  });

  const activeTasks = tasks.filter(t => !t.completed);
  const completedTasks = tasks.filter(t => t.completed);

  const renderTask = (task: TodoItem) => {
    const isOverdue = task.due_date && new Date(task.due_date) < new Date() && !task.completed;
    const category = autoCategory(task);
    const categoryInfo = getCategoryInfo(category);

    return (
      <div
        key={task.id}
        className={`border rounded-lg p-4 transition-all ${
          task.completed
            ? 'bg-gray-900 opacity-60 border-gray-700'
            : isOverdue
            ? 'bg-red-900/20 border-red-600'
            : 'bg-gray-700 hover:shadow-md border-gray-600'
        }`}
      >
        <div className="flex items-start space-x-3">
          <button
            onClick={() => toggleTask(task.id)}
            className="mt-1 flex-shrink-0"
            title="Toggle completion"
          >
            {task.completed ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <Circle className="h-5 w-5 text-gray-400 hover:text-gray-600" />
            )}
          </button>

          <div className="flex-1 min-w-0">
            {/* Badges row */}
            <div className="flex items-center space-x-2 mb-2 flex-wrap gap-1">
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${categoryInfo.color}`}>
                {categoryInfo.icon} {categoryInfo.label}
              </span>
              
              <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                task.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                task.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                'bg-blue-100 text-blue-700'
              }`}>
                {task.priority?.toUpperCase() || 'NORMAL'}
              </span>
              
              {task.due_date && (
                <span className={`text-xs font-medium ${isOverdue ? 'text-red-600' : 'text-gray-600'}`}>
                  <Clock className="h-3 w-3 inline mr-1" />
                  {formatDate(task.due_date)}
                </span>
              )}
              
              {task.time_estimate && (
                <span className="text-xs text-gray-500">
                  ~{task.time_estimate}
                </span>
              )}
            </div>

            {/* Task action - editable */}
            {editingTaskId === task.id ? (
              <div className="flex items-center space-x-2 mb-2">
                <input
                  type="text"
                  value={editingText}
                  onChange={(e) => setEditingText(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') saveEdit(task.id);
                    if (e.key === 'Escape') cancelEdit();
                  }}
                  className="flex-1 px-3 py-2 border border-red-500 bg-gray-600 text-white rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
                  autoFocus
                />
                <button
                  onClick={() => saveEdit(task.id)}
                  className="p-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  title="Save"
                >
                  <Save className="h-4 w-4" />
                </button>
                <button
                  onClick={cancelEdit}
                  className="p-2 bg-gray-600 text-gray-300 rounded-lg hover:bg-gray-500"
                  title="Cancel"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2 mb-2 group">
                <h3 className={`flex-1 font-medium text-white break-words ${task.completed ? 'line-through' : ''}`}>
                  {task.action}
                </h3>
                {!task.completed && (
                  <button
                    onClick={() => startEditing(task)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600 rounded"
                    title="Edit task"
                  >
                    <Edit2 className="h-4 w-4 text-gray-400" />
                  </button>
                )}
              </div>
            )}

            {/* Category dropdown - only show for active tasks */}
            {!task.completed && (
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-400">Move to:</span>
                <select
                  value={category}
                  onChange={(e) => updateCategory(task.id, e.target.value as TodoItem['category'])}
                  className="text-xs px-2 py-1 rounded border border-gray-600 bg-gray-600 text-white hover:bg-gray-500 cursor-pointer focus:ring-2 focus:ring-red-500 focus:border-red-500"
                >
                  <option value="urgent-important">🔴 Urgent & Important</option>
                  <option value="important-not-urgent">🟠 Important</option>
                  <option value="urgent-not-important">🟡 Urgent</option>
                  <option value="neither">⚪ Low Priority</option>
                </select>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-1">
            {/* Push to Team Board Button */}
            <button
              onClick={() => pushToTeamBoard(task.id)}
              disabled={pushingTaskId === task.id || task.completed}
              className="p-1 hover:bg-purple-900/20 rounded flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Push to Team Board"
            >
              {pushingTaskId === task.id ? (
                <RefreshCw className="h-4 w-4 text-purple-400 animate-spin" />
              ) : (
                <Users className="h-4 w-4 text-purple-400" />
              )}
            </button>

            {/* Google Tasks Sync Button */}
            {task.google_task_id ? (
              <button
                className="p-1 rounded flex-shrink-0 cursor-default"
                title="Synced to Google Tasks"
                disabled
              >
                <CheckSquare className="h-4 w-4 text-green-500" />
              </button>
            ) : (
              <button
                onClick={() => syncToGoogleTasks(task.id)}
                disabled={syncingTaskId === task.id || task.completed}
                className="p-1 hover:bg-blue-900/20 rounded flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Sync to Google Tasks"
              >
                {syncingTaskId === task.id ? (
                  <RefreshCw className="h-4 w-4 text-blue-400 animate-spin" />
                ) : (
                  <CheckSquare className="h-4 w-4 text-blue-400" />
                )}
              </button>
            )}
            <button
              onClick={() => openCalendarModal(task)}
              className="p-1 hover:bg-blue-900/20 rounded flex-shrink-0"
              title="Add to Google Calendar"
            >
              <Calendar className="h-4 w-4 text-blue-400" />
            </button>
            <button
              onClick={() => deleteTask(task.id)}
              className="p-1 hover:bg-red-900/20 rounded flex-shrink-0"
              title="Delete task"
            >
              <Trash2 className="h-4 w-4 text-red-400" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  const { suggestedDate, suggestedTime } = selectedTask
    ? getSuggestedDateTime(selectedTask)
    : { suggestedDate: '', suggestedTime: '' };

  return (
    <div className="space-y-6">
      {/* Calendar Modal */}
      {selectedTask && (
        <CalendarModal
          isOpen={calendarModalOpen}
          onClose={() => {
            setCalendarModalOpen(false);
            setSelectedTask(null);
          }}
          title={selectedTask.action}
          suggestedDate={suggestedDate}
          suggestedTime={suggestedTime}
          description={`Priority: ${selectedTask.priority}\nEstimate: ${selectedTask.time_estimate || 'N/A'}`}
          priority={selectedTask.priority as 'low' | 'medium' | 'high' | 'urgent'}
          timeEstimate={selectedTask.time_estimate}
          dueDate={selectedTask.due_date}
        />
      )}
      {/* Navigation Tabs */}
      {onNavigate && (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-3">
          <nav className="flex space-x-2">
            <button
              onClick={() => onNavigate('triage')}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-300 hover:bg-gray-700"
            >
              📧 Email Triage
            </button>
            <button
              onClick={() => onNavigate('todo')}
              className="px-4 py-2 rounded-lg font-medium text-sm bg-red-500 text-white"
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

      {/* Add New Task Form */}
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4">
        <div className="flex items-start space-x-3">
          <Plus className="h-6 w-6 text-red-600 mt-2 flex-shrink-0" />
          <div className="flex-1 space-y-3">
            <input
              type="text"
              value={newTaskText}
              onChange={(e) => setNewTaskText(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !addingTask) addNewTask();
              }}
              placeholder="Add a new task... (Press Enter to add)"
              className="w-full px-4 py-3 border border-gray-600 bg-gray-700 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 text-white placeholder-gray-400"
            />

            <div className="flex items-center space-x-3 flex-wrap gap-2">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-300">Priority:</label>
                <select
                  value={newTaskPriority}
                  onChange={(e) => setNewTaskPriority(e.target.value)}
                  className="px-3 py-1.5 border border-gray-600 bg-gray-700 text-white rounded-lg text-sm focus:ring-2 focus:ring-red-500"
                >
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-300">Due Date:</label>
                <input
                  type="date"
                  value={newTaskDueDate}
                  onChange={(e) => setNewTaskDueDate(e.target.value)}
                  className="px-3 py-1.5 border border-gray-600 bg-gray-700 text-white rounded-lg text-sm focus:ring-2 focus:ring-red-500"
                />
              </div>

              <button
                onClick={addNewTask}
                disabled={!newTaskText.trim() || addingTask}
                className="ml-auto px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed font-medium text-sm flex items-center space-x-2"
              >
                {addingTask ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Adding...</span>
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    <span>Add Task</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Header with filters */}
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-bold text-white">Todo List</h2>

            <a
              href="https://tasks.google.com"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors flex items-center space-x-2"
              title="Open Google Tasks"
            >
              <CheckSquare className="h-4 w-4" />
              <span>Open Google Tasks</span>
            </a>

            <button
              onClick={syncFromTeamBoard}
              disabled={syncingFromTeam}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white text-sm font-medium rounded-lg transition-colors flex items-center space-x-2"
              title="Sync status updates from team board"
            >
              {syncingFromTeam ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              <span>Sync from Team</span>
            </button>

            <div className="flex items-center space-x-3 text-sm">
              <span className="text-gray-300">{activeTasks.length} active</span>
              <span className="text-gray-500">•</span>
              <span className="text-gray-300">{completedTasks.length} completed</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Status Filter */}
            <div className="flex space-x-1">
              <button
                onClick={() => setFilter('active')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'active' ? 'bg-red-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                Active
              </button>
              <button
                onClick={() => setFilter('completed')}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  filter === 'completed' ? 'bg-red-600 text-white' : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                Completed
              </button>
            </div>

            {/* Category Filter */}
            {filter === 'active' && (
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4 text-gray-400" />
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="text-sm px-3 py-1.5 rounded-lg border border-gray-600 bg-gray-700 text-white hover:bg-gray-600 cursor-pointer focus:ring-2 focus:ring-red-500"
                >
                  <option value="all">All Categories</option>
                  <option value="urgent-important">🔴 Urgent & Important</option>
                  <option value="important-not-urgent">🟠 Important</option>
                  <option value="urgent-not-important">🟡 Urgent</option>
                  <option value="neither">⚪ Low Priority</option>
                </select>
              </div>
            )}

            <button
              onClick={fetchTasks}
              className="p-2 hover:bg-gray-700 rounded-lg"
              title="Refresh"
            >
              <RefreshCw className={`h-5 w-5 text-gray-300 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Task List */}
      {loading ? (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-8 text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2 text-gray-400" />
          <p className="text-gray-300">Loading tasks...</p>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-8 text-center">
          <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-3" />
          <p className="text-lg font-medium text-white">
            {filter === 'completed' ? 'No completed tasks yet' : 'All caught up!'}
          </p>
          <p className="text-sm text-gray-400 mt-2">
            {filter === 'completed' ? 'Complete some tasks to see them here' : 'No active tasks'}
          </p>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-4">
          <div className="space-y-3">
            {filteredTasks.map(task => renderTask(task))}
          </div>
        </div>
      )}
    </div>
  );
}
