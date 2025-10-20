'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  ArrowLeft, Check, Save, Sparkles, AlertTriangle
} from 'lucide-react';

interface ChiliHeadStep {
  completed: boolean;
  notes: string;
}

interface ChiliHeadProgress {
  senseOfBelonging: ChiliHeadStep;
  clearDirection: ChiliHeadStep;
  preparation: ChiliHeadStep;
  support: ChiliHeadStep;
  accountability: ChiliHeadStep;
}

export default function NewDelegationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Pre-fill from URL params (when coming from email triage)
  const taskFromUrl = searchParams?.get('task') || '';
  const assigneeFromUrl = searchParams?.get('assignee') || '';
  const dueDateFromUrl = searchParams?.get('due') || '';

  const [formData, setFormData] = useState({
    taskDescription: taskFromUrl,
    assignedTo: assigneeFromUrl,
    dueDate: dueDateFromUrl,
    followUpDate: '',
    priority: 'medium' as 'low' | 'medium' | 'high',
    status: 'planning' as 'planning' | 'active',
    chiliheadProgress: {
      senseOfBelonging: { completed: false, notes: '' },
      clearDirection: { completed: false, notes: '' },
      preparation: { completed: false, notes: '' },
      support: { completed: false, notes: '' },
      accountability: { completed: false, notes: '' }
    } as ChiliHeadProgress
  });

  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const commitmentItems = [
    { 
      key: 'senseOfBelonging', 
      label: 'SENSE OF BELONGING',
      description: 'Make them feel valued and included',
      color: 'from-yellow-400 to-yellow-500',
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-800',
      placeholder: 'How did you give them ownership? What area of responsibility?'
    },
    { 
      key: 'clearDirection', 
      label: 'CLEAR DIRECTION',
      description: 'They know exactly what success looks like',
      color: 'from-orange-400 to-orange-500',
      bgColor: 'bg-orange-50',
      textColor: 'text-orange-800',
      placeholder: 'What does good look like? How will they know they succeeded?'
    },
    { 
      key: 'preparation', 
      label: 'PREPARATION',
      description: 'They have everything needed to succeed',
      color: 'from-red-400 to-red-500',
      bgColor: 'bg-red-50',
      textColor: 'text-red-800',
      placeholder: 'What resources, training, or tools do they need?'
    },
    { 
      key: 'support', 
      label: 'SUPPORT',
      description: 'Ongoing help and resources available',
      color: 'from-red-500 to-red-600',
      bgColor: 'bg-red-50',
      textColor: 'text-red-800',
      placeholder: 'How will you support them? Who can they ask for help?'
    },
    { 
      key: 'accountability', 
      label: 'ACCOUNTABILITY',
      description: 'Follow-up expectations are crystal clear',
      color: 'from-purple-500 to-purple-600',
      bgColor: 'bg-purple-50',
      textColor: 'text-purple-800',
      placeholder: 'When will you check in? How will you follow up?'
    }
  ];

  const updateChiliheadProgress = (key: string, field: 'completed' | 'notes', value: boolean | string) => {
    setFormData(prev => ({
      ...prev,
      chiliheadProgress: {
        ...prev.chiliheadProgress,
        [key]: {
          ...prev.chiliheadProgress[key as keyof ChiliHeadProgress],
          [field]: value
        }
      }
    }));
  };

  const completedCount = Object.values(formData.chiliheadProgress).filter(step => step.completed).length;
  const canActivate = completedCount > 0 && formData.dueDate;

  const handleSave = async (activate: boolean = false) => {
    if (!formData.taskDescription || !formData.assignedTo) {
      alert('🌶️ Please provide task description and assignee');
      return;
    }

    if (activate && !canActivate) {
      alert('🌶️ Complete at least 1 ChiliHead step and set a due date to activate');
      return;
    }

    setSaving(true);
    try {
      const delegation = {
        ...formData,
        status: activate ? 'active' : 'planning'
      };

      const response = await fetch('/api/backend/delegations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(delegation)
      });

      if (response.ok) {
        const message = activate 
          ? `🌶️ Delegation activated with ${completedCount}/5 ChiliHead steps!`
          : '🌶️ Delegation saved as draft!';
        alert(message);
        router.push('/delegations');
      } else {
        throw new Error('Failed to save delegation');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('❌ Failed to save delegation');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-600 to-orange-600 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => router.push('/delegations')}
            className="flex items-center text-red-100 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Back
          </button>
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium">ChiliHead Progress:</span>
            <div className="flex items-center space-x-1">
              <span className="text-lg font-bold">{completedCount}/5</span>
              <Sparkles className="h-4 w-4" />
            </div>
          </div>
        </div>
        <h1 className="text-2xl font-bold">🌶️ New Delegation</h1>
        <p className="text-red-100 text-sm mt-1">5-Pillar Leadership Development</p>
      </div>

      {/* Task Description */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Task Description *
        </label>
        <textarea
          value={formData.taskDescription}
          onChange={(e) => setFormData(prev => ({ ...prev, taskDescription: e.target.value }))}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
          rows={3}
          placeholder="What needs to be accomplished?"
          required
        />
      </div>

      {/* Assignment Details */}
      <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Assignment Details</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Assign To *
          </label>
          <input
            type="text"
            value={formData.assignedTo}
            onChange={(e) => setFormData(prev => ({ ...prev, assignedTo: e.target.value }))}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            placeholder="Team member name..."
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Due Date
            </label>
            <input
              type="date"
              value={formData.dueDate}
              onChange={(e) => setFormData(prev => ({ ...prev, dueDate: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
            <p className="text-xs text-gray-500 mt-1">Required for activation</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Follow-up Date
            </label>
            <input
              type="date"
              value={formData.followUpDate}
              onChange={(e) => setFormData(prev => ({ ...prev, followUpDate: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Priority
          </label>
          <select
            value={formData.priority}
            onChange={(e) => setFormData(prev => ({ ...prev, priority: e.target.value as 'low' | 'medium' | 'high' }))}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      {/* ChiliHead 5-Pillar Commitment */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-1">The CHILIHEAD</h2>
          <h2 className="text-2xl font-bold text-red-600 mb-3">COMMITMENT</h2>
          <p className="text-sm text-gray-600 mb-4">
            Progress: {completedCount}/5 Steps • Build this over time with your team member
          </p>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-red-500 to-red-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${(completedCount / 5) * 100}%` }}
            />
          </div>
        </div>

        <div className="space-y-4">
          {commitmentItems.map((item, index) => {
            const stepData = formData.chiliheadProgress[item.key as keyof ChiliHeadProgress];
            const isActive = activeStep === item.key;

            return (
              <div
                key={item.key}
                className={`relative p-4 rounded-lg border-2 transition-all ${
                  stepData.completed
                    ? `${item.bgColor} border-${item.key === 'accountability' ? 'purple' : item.key === 'senseOfBelonging' ? 'yellow' : item.key === 'clearDirection' ? 'orange' : 'red'}-300 shadow-md`
                    : isActive
                    ? 'bg-gray-50 border-blue-300 shadow-sm'
                    : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    <div className={`bg-gradient-to-r ${item.color} text-white w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold`}>
                      {stepData.completed ? <Check className="w-4 h-4" /> : index + 1}
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className={`font-bold text-lg ${stepData.completed ? item.textColor : 'text-gray-600'}`}>
                        {item.label}
                      </h3>
                      <div className="flex items-center space-x-2">
                        {stepData.completed && (
                          <span className="text-green-600 text-sm font-medium flex items-center">
                            <Check className="w-4 h-4 mr-1" /> Complete
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => setActiveStep(isActive ? null : item.key)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          {isActive ? 'Close' : stepData.completed ? 'Edit' : 'Work On This'}
                        </button>
                      </div>
                    </div>
                    <p className={`text-sm ${stepData.completed ? item.textColor : 'text-gray-500'} mb-2`}>
                      {item.description}
                    </p>

                    {isActive && (
                      <div className="mt-3 space-y-3">
                        <textarea
                          value={stepData.notes}
                          onChange={(e) => updateChiliheadProgress(item.key, 'notes', e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          rows={3}
                          placeholder={item.placeholder}
                        />
                        <label className="flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={stepData.completed}
                            onChange={(e) => updateChiliheadProgress(item.key, 'completed', e.target.checked)}
                            className="w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500 mr-2"
                          />
                          <span className="text-sm font-medium text-gray-700">Mark as complete</span>
                        </label>
                      </div>
                    )}

                    {stepData.completed && stepData.notes && !isActive && (
                      <div className="mt-2 p-3 bg-white bg-opacity-60 rounded text-sm">
                        <strong className="text-gray-700">Notes:</strong> <span className="text-gray-600">{stepData.notes}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Sparkles className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <strong>Pro Tip:</strong> You don't need to complete all steps at once! Save as draft and continue building the ChiliHead Commitment over time as you work with your team member.
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3 pb-8">
        <button
          onClick={() => handleSave(false)}
          disabled={saving}
          className="w-full bg-gray-600 hover:bg-gray-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center"
        >
          <Save className="w-5 h-5 mr-2" />
          {saving ? 'Saving...' : 'Save as Draft'}
        </button>

        {canActivate ? (
          <button
            onClick={() => handleSave(true)}
            disabled={saving}
            className="w-full bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-4 rounded-lg font-bold transition-colors flex items-center justify-center"
          >
            <Sparkles className="w-5 h-5 mr-2" />
            {saving ? 'Activating...' : `🌶️ Activate Delegation (${completedCount}/5 steps)`}
          </button>
        ) : (
          <div className="w-full bg-gray-300 text-gray-600 py-3 px-4 rounded-lg font-semibold text-center flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {completedCount === 0 && !formData.dueDate && "Complete 1+ ChiliHead step + set due date to activate"}
            {completedCount === 0 && formData.dueDate && "Complete at least 1 ChiliHead step to activate"}
            {completedCount > 0 && !formData.dueDate && "Set due date to activate"}
          </div>
        )}
      </div>
    </div>
  );
}
