'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import TriagePage from './components/TriagePage';
import TodoPage from './components/TodoPage';
import DelegationsPage from './delegations/page';
import OperationsChat from './components/OperationsChat';
import {
  Inbox, CheckSquare, Users, Brain, Sparkles
} from 'lucide-react';

export default function OpsManagerDashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const [currentPage, setCurrentPage] = useState<'triage' | 'todo' | 'delegations'>('triage');
  const [taskCount, setTaskCount] = useState(0);
  const [delegationCount, setDelegationCount] = useState(0);
  const [dailyDigest, setDailyDigest] = useState<string>("");
  const [operations, setOperations] = useState<any[]>([]);

  // Fetch task count for badge
  const fetchTaskCount = async () => {
    try {
      const response = await fetch('/api/backend/state/tasks?completed=false');
      const data = await response.json();
      setTaskCount(data.count || 0);
    } catch (error) {
      console.error('Failed to fetch task count:', error);
    }
  };

  // Fetch delegation count
  const fetchDelegationCount = async () => {
    try {
      const response = await fetch('/api/backend/delegations?status=active');
      const data = await response.json();
      setDelegationCount(data.delegations?.length || 0);
    } catch (error) {
      console.error('Failed to fetch delegation count:', error);
    }
  };

  // Fetch daily digest for chat context
  const fetchDailyDigest = async () => {
    try {
      const response = await fetch('/api/backend/daily-digest');
      const data = await response.json();
      setDailyDigest(data.digest || "");
    } catch (error) {
      console.error('Failed to fetch daily digest:', error);
    }
  };

  // Fetch operations for chat context
  const fetchOperations = async () => {
    try {
      const response = await fetch('/api/backend/state/tasks?completed=false');
      const data = await response.json();
      setOperations(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch operations:', error);
    }
  };

  useEffect(() => {
    fetchTaskCount();
    fetchDelegationCount();
    fetchDailyDigest();
    fetchOperations();
    // Refresh counts every 30 seconds
    const interval = setInterval(() => {
      fetchTaskCount();
      fetchDelegationCount();
      fetchOperations();
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  // Refresh counts when switching pages
  useEffect(() => {
    if (currentPage === 'todo') {
      fetchTaskCount();
    } else if (currentPage === 'delegations') {
      fetchDelegationCount();
    }
  }, [currentPage]);

  const handleAddToTodo = async (items: any[], threadId?: string) => {
    try {
      const response = await fetch('/api/backend/state/tasks/add-bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          tasks: items,
          thread_id: threadId
        })
      });
      
      if (response.ok) {
        // Update task count
        fetchTaskCount();
        
        // Show notification
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        toast.textContent = `✓ Added ${items.length} ${items.length === 1 ? 'task' : 'tasks'} to todo list`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
      }
    } catch (error) {
      console.error('Failed to add tasks:', error);
      // Show error notification
      const toast = document.createElement('div');
      toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
      toast.textContent = '✗ Failed to add tasks';
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Header with Navigation */}
      <header className="bg-gray-800 shadow-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              {/* Logo */}
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-red-500 to-orange-500 rounded-lg">
                  <Brain className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">🌶️ ChiliHead OpsManager</h1>
                  <p className="text-xs text-gray-400">AI Email + Leadership Delegations</p>
                </div>
              </div>

              {/* Navigation Tabs */}
              <nav className="flex space-x-1">
                <button
                  onClick={() => setCurrentPage('triage')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center space-x-2 ${
                    currentPage === 'triage'
                      ? 'bg-red-500 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <Inbox className="h-4 w-4" />
                  <span>Email Triage</span>
                  <span className="ml-2 px-2 py-0.5 text-xs bg-white/20 rounded-full">
                    AI
                  </span>
                </button>
                
                <button
                  onClick={() => setCurrentPage('todo')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center space-x-2 ${
                    currentPage === 'todo'
                      ? 'bg-red-500 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <CheckSquare className="h-4 w-4" />
                  <span>Todo List</span>
                  {taskCount > 0 && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-red-600 text-white rounded-full">
                      {taskCount}
                    </span>
                  )}
                </button>

                <button
                  onClick={() => setCurrentPage('delegations')}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors flex items-center space-x-2 ${
                    currentPage === 'delegations'
                      ? 'bg-red-500 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <Users className="h-4 w-4" />
                  <span>🌶️ Delegations</span>
                  {delegationCount > 0 && (
                    <span className="ml-2 px-2 py-0.5 text-xs bg-orange-600 text-white rounded-full">
                      {delegationCount}
                    </span>
                  )}
                </button>
              </nav>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-300">
                <Sparkles className="h-4 w-4 text-yellow-400" />
                <span>Powered by GPT-4</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentPage === 'triage' ? (
          <TriagePage onAddToTodo={handleAddToTodo} />
        ) : currentPage === 'todo' ? (
          <TodoPage />
        ) : (
          <DelegationsPage />
        )}
      </div>

      {/* Operations Chat - Available on all pages */}
      <OperationsChat dailyDigest={dailyDigest} operations={operations} />
    </div>
  );
}
