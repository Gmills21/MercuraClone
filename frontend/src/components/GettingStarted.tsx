import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, Users, Sparkles, Camera, X, CheckCircle,
  ArrowRight, ChevronRight, Lightbulb, HelpCircle
} from 'lucide-react';
import { api } from '../services/api';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  action_link: string;
  action_text: string;
  completed: boolean;
  icon: string;
}

export const GettingStarted = () => {
  const navigate = useNavigate();
  const [checklist, setChecklist] = useState<{
    steps: OnboardingStep[];
    completed_count: number;
    total_steps: number;
    progress_percent: number;
    is_complete: boolean;
    next_step?: OnboardingStep;
  } | null>(null);
  const [showTips, setShowTips] = useState(true);
  const [currentTip, setCurrentTip] = useState(0);

  const tips = [
    {
      title: "Smart Quote is Your Superpower",
      content: "Paste any RFQ email and AI extracts the items automatically. Saves 16 minutes per quote."
    },
    {
      title: "Check Alerts Daily",
      content: "The bell icon shows new RFQs and quotes needing follow-up. Red = urgent."
    },
    {
      title: "Customer Intelligence",
      content: "Health scores tell you which relationships need attention. 80+ is excellent."
    },
    {
      title: "Track Your Impact",
      content: "Business Impact shows time saved and ROI. Most users see 400%+ ROI in first month."
    }
  ];

  useEffect(() => {
    loadChecklist();
  }, []);

  const loadChecklist = async () => {
    try {
      const res = await api.get('/onboarding/checklist');
      setChecklist(res.data);
    } catch (err) {
      console.error('Failed to load checklist:', err);
    }
  };

  const markComplete = async (stepId: string) => {
    try {
      await api.post(`/onboarding/complete/${stepId}`);
      loadChecklist();
    } catch (err) {
      console.error('Failed to mark complete:', err);
    }
  };

  const dismissChecklist = async () => {
    try {
      await api.post('/onboarding/dismiss');
      setChecklist(prev => prev ? { ...prev, is_complete: true } : null);
    } catch (err) {
      console.error('Failed to dismiss:', err);
    }
  };

  if (!checklist || checklist.is_complete) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Lightbulb className="text-blue-600" size={20} />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-blue-900">Quick Tip</h3>
              <button 
                onClick={() => setCurrentTip((prev) => (prev + 1) % tips.length)}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Next tip →
              </button>
            </div>
            <p className="font-medium text-blue-900">{tips[currentTip].title}</p>
            <p className="text-sm text-blue-700 mt-1">{tips[currentTip].content}</p>
          </div>
        </div>
      </div>
    );
  }

  const nextStep = checklist.next_step;

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gradient-to-r from-orange-50 to-amber-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Sparkles className="text-orange-600" size={20} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Getting Started</h3>
              <p className="text-sm text-gray-600">
                {checklist.completed_count} of {checklist.total_steps} completed
              </p>
            </div>
          </div>
          <button 
            onClick={dismissChecklist}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Dismiss"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-orange-500 rounded-full transition-all"
            style={{ width: `${checklist.progress_percent}%` }}
          />
        </div>
      </div>

      {/* Next Step Highlight */}
      {nextStep && (
        <div className="p-5 border-b border-gray-100">
          <p className="text-sm text-gray-500 mb-2">Recommended next:</p>
          <div className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div>
              <h4 className="font-semibold text-gray-900">{nextStep.title}</h4>
              <p className="text-sm text-gray-600 mt-1">{nextStep.description}</p>
            </div>
            <button
              onClick={() => {
                markComplete(nextStep.id);
                navigate(nextStep.action_link);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-colors whitespace-nowrap"
            >
              {nextStep.action_text}
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* All Steps (Collapsible) */}
      <details className="group">
        <summary className="px-5 py-3 cursor-pointer text-sm font-medium text-gray-600 hover:bg-gray-50 flex items-center justify-between">
          <span>View all steps</span>
          <ChevronRight size={16} className="group-open:rotate-90 transition-transform" />
        </summary>
        <div className="divide-y divide-gray-100">
          {checklist.steps.map((step) => (
            <div 
              key={step.id}
              className={`px-5 py-3 flex items-center gap-3 ${step.completed ? 'bg-gray-50' : ''}`}
            >
              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                step.completed ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
              }`}>
                {step.completed ? <CheckCircle size={14} /> : <div className="w-2 h-2 bg-gray-300 rounded-full" />}
              </div>
              <span className={`text-sm ${step.completed ? 'text-gray-500 line-through' : 'text-gray-700'}`}>
                {step.title}
              </span>
            </div>
          ))}
        </div>
      </details>
    </div>
  );
};

export default GettingStarted;
