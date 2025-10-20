'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Users, Plus, AlertTriangle, Calendar, Clock,
  CheckCircle, ArrowRight, TrendingUp
} from 'lucide-react';

interface ChiliHeadProgress {
  senseOfBelonging: { completed: boolean; notes: string };
  clearDirection: { completed: boolean; notes: string };
  preparation: { completed: boolean; notes: string };
  support: { completed: boolean; notes: string };
  accountability: { completed: boolean; notes: string };
}

interface Delegation {
  id: string;
  task_description: string;
  assigned_to: string;
  due_date?: string;
  follow_up_date?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'planning' | 'active' | 'completed' | 'on-hold';
  created_at: string;
  chilihead_progress: ChiliHeadProgress;
}

export default function DelegationsPage() {
  const router = useRouter();
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'overdue' | 'due_soon'>('all');

  useEffect(() => {
    fetchDelegations();
  }, []);

  const fetchDelegations = async () => {
    try {
      const response = await fetch('/api/backend/delegations');
      if (response.ok) {
        const data = await response.json();
        setDelegations(data.delegations || []);
      }
    } catch (error) {
      console.error('Failed to fetch delegations:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCompletedSteps = (progress: ChiliHeadProgress) => {
    return Object.values(progress).filter(step => step.completed).length;
  };

  const isOverdue = (dueDate?: string) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const isDueSoon = (dueDate?: string) => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    const threeDays = new Date();
    threeDays.setDate(threeDays.getDate() + 3);
    return due <= threeDays && due >= new Date();
  };

  const filteredDelegations = delegations.filter(d => {
    if (filter === 'all') return true;
    if (filter === 'active') return d.status === 'active';
    if (filter === 'overdue') return isOverdue(d.due_date) && d.status === 'active';
    if (filter === 'due_soon') return isDueSoon(d.due_date);
    return true;
  });

  const activeDelegationsCount = delegations.filter(d => d.status === 'active').length;
  const overdueDelegationsCount = delegations.filter(d => isOverdue(d.due_date) && d.status === 'active').length;
  const dueSoonCount = delegations.filter(d => isDueSoon(d.due_date)).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white bg-opacity-20 rounded-lg">
              <Users className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">🌶️ ChiliHead Delegations</h1>
              <p className="text-red-100 text-sm">5-Pillar Leadership Development System</p>
            </div>
          </div>
          <button
            onClick={() => router.push('/delegations/new')}
            className="flex items-center space-x-2 bg-white text-red-600 px-4 py-2 rounded-lg font-semibold hover:bg-red-50 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>New Delegation</span>
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6">
          <button
            onClick={() => setFilter('active')}
            className={`p-4 rounded-lg transition-all ${
              filter === 'active' ? 'bg-white text-red-600' : 'bg-white bg-opacity-20 hover:bg-opacity-30'
            }`}
          >
            <div className="text-2xl font-bold">{activeDelegationsCount}</div>
            <div className={`text-sm ${filter === 'active' ? 'text-red-600' : 'text-red-100'}`}>
              Active
            </div>
          </button>
          <button
            onClick={() => setFilter('due_soon')}
            className={`p-4 rounded-lg transition-all ${
              filter === 'due_soon' ? 'bg-white text-yellow-600' : 'bg-white bg-opacity-20 hover:bg-opacity-30'
            }`}
          >
            <div className="text-2xl font-bold">{dueSoonCount}</div>
            <div className={`text-sm ${filter === 'due_soon' ? 'text-yellow-600' : 'text-red-100'}`}>
              Due Soon
            </div>
          </button>
          <button
            onClick={() => setFilter('overdue')}
            className={`p-4 rounded-lg transition-all ${
              filter === 'overdue' ? 'bg-white text-red-600' : 'bg-white bg-opacity-20 hover:bg-opacity-30'
            }`}
          >
            <div className="text-2xl font-bold">{overdueDelegationsCount}</div>
            <div className={`text-sm ${filter === 'overdue' ? 'text-red-600' : 'text-red-100'}`}>
              Overdue
            </div>
          </button>
        </div>
      </div>

      {/* Delegations List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading delegations...</p>
        </div>
      ) : filteredDelegations.length === 0 ? (
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-12 text-center">
          <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">🌶️ ChiliHead Delegation Hub</h2>
          <p className="text-gray-300 mb-6">
            Start developing your team with the 5-Pillar Methodology
          </p>

          <div className="bg-gray-700 rounded-lg p-6 max-w-md mx-auto mb-6">
            <h3 className="font-semibold text-white mb-3">The ChiliHead Commitment:</h3>
            <div className="space-y-2 text-left">
              {[
                'Sense of Belonging',
                'Clear Direction',
                'Preparation',
                'Support',
                'Accountability'
              ].map((item) => (
                <div key={item} className="flex items-center text-sm text-gray-300">
                  <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => router.push('/delegations/new')}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-flex items-center space-x-2"
          >
            <span>🌶️ Create Your First Delegation</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredDelegations.map((delegation) => {
            const completedSteps = getCompletedSteps(delegation.chilihead_progress);
            const overdue = isOverdue(delegation.due_date);

            return (
              <button
                key={delegation.id}
                onClick={() => router.push(`/delegations/${delegation.id}`)}
                className={`w-full text-left bg-gray-800 border border-gray-700 rounded-lg shadow-sm p-6 border-l-4 hover:shadow-md transition-all ${
                  overdue ? 'border-l-red-500 bg-red-900/20' : 'border-l-green-500'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-1">
                      {delegation.task_description}
                    </h3>
                    <p className="text-sm text-gray-300">
                      Assigned to: <span className="font-medium">{delegation.assigned_to}</span>
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      delegation.status === 'active' ? 'bg-green-100 text-green-800' :
                      delegation.status === 'planning' ? 'bg-yellow-100 text-yellow-800' :
                      delegation.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {delegation.status}
                  </span>
                </div>

                {delegation.due_date && (
                  <div className="flex items-center text-sm mb-3">
                    <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                    <span className={overdue ? 'text-red-400 font-medium' : 'text-gray-300'}>
                      Due: {new Date(delegation.due_date).toLocaleDateString()}
                      {overdue && ' (Overdue!)'}
                    </span>
                  </div>
                )}

                {/* Progress Bar */}
                <div className="mb-3">
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-300 font-medium">ChiliHead Progress</span>
                    <span className="text-gray-300">{completedSteps}/5</span>
                  </div>
                  <div className="flex space-x-1">
                    {['senseOfBelonging', 'clearDirection', 'preparation', 'support', 'accountability'].map((key, index) => {
                      const pillarKey = key as keyof ChiliHeadProgress;
                      const colors = ['bg-yellow-500', 'bg-orange-500', 'bg-red-400', 'bg-red-500', 'bg-purple-500'];
                      return (
                        <div
                          key={key}
                          className={`flex-1 h-2 rounded-full ${
                            delegation.chilihead_progress[pillarKey].completed
                              ? colors[index]
                              : 'bg-gray-200'
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Created: {new Date(delegation.created_at).toLocaleDateString()}</span>
                  <span className="flex items-center text-red-400">
                    View Details <ArrowRight className="h-3 w-3 ml-1" />
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
