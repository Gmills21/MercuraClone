import React from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Clock, DollarSign, Users, ArrowRight } from 'lucide-react';

interface BusinessImpactWidgetProps {
  timeSaved?: number;
  roi?: number;
  quotesCreated?: number;
}

export const BusinessImpactWidget: React.FC<BusinessImpactWidgetProps> = ({
  timeSaved = 0,
  roi = 0,
  quotesCreated = 0
}) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <TrendingUp size={18} className="text-green-600" />
          Business Impact
        </h3>
        <button 
          type="button"
          onClick={() => navigate('/impact')}
          className="text-sm text-orange-600 hover:text-orange-700 cursor-pointer"
        >
          Details →
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{timeSaved}h</div>
          <div className="text-xs text-gray-500">Time Saved</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{roi}%</div>
          <div className="text-xs text-gray-500">ROI</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">{quotesCreated}</div>
          <div className="text-xs text-gray-500">Quotes</div>
        </div>
      </div>
    </div>
  );
};

interface CustomerIntelligenceWidgetProps {
  vipCount?: number;
  atRiskCount?: number;
  healthScore?: number;
}

export const CustomerIntelligenceWidget: React.FC<CustomerIntelligenceWidgetProps> = ({
  vipCount = 0,
  atRiskCount = 0,
  healthScore = 0
}) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <Users size={18} className="text-blue-600" />
          Customer Health
        </h3>
        <button 
          type="button"
          onClick={() => navigate('/intelligence')}
          className="text-sm text-orange-600 hover:text-orange-700 cursor-pointer"
        >
          Details →
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-700">VIP Customers</span>
          </div>
          <span className="font-semibold text-green-700">{vipCount}</span>
        </div>

        {atRiskCount > 0 && (
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
              <span className="text-sm text-gray-700">At Risk</span>
            </div>
            <span className="font-semibold text-red-700">{atRiskCount}</span>
          </div>
        )}

        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span className="text-sm text-gray-700">Avg Health Score</span>
          <span className={`font-semibold ${
            healthScore >= 80 ? 'text-green-600' : 
            healthScore >= 60 ? 'text-blue-600' : 'text-amber-600'
          }`}>{healthScore}/100</span>
        </div>
      </div>
    </div>
  );
};

interface QuickActionsWidgetProps {
  onCreateQuote?: () => void;
  onCaptureImage?: () => void;
}

export const QuickActionsWidget: React.FC<QuickActionsWidgetProps> = ({
  onCreateQuote,
  onCaptureImage
}) => {
  const navigate = useNavigate();

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
      
      <div className="space-y-2">
        <button
          onClick={() => onCreateQuote ? onCreateQuote() : navigate('/quotes/new')}
          className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg hover:bg-orange-50 border border-gray-200 hover:border-orange-200 transition-colors"
        >
          <div className="p-2 bg-orange-100 rounded-lg">
            <DollarSign className="text-orange-600" size={16} />
          </div>
          <div>
            <div className="font-medium text-gray-900">Create Smart Quote</div>
            <div className="text-sm text-gray-500">AI-powered extraction</div>
          </div>
        </button>

        <button
          onClick={() => onCaptureImage ? onCaptureImage() : navigate('/camera')}
          className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg hover:bg-purple-50 border border-gray-200 hover:border-purple-200 transition-colors"
        >
          <div className="p-2 bg-purple-100 rounded-lg">
            <Clock className="text-purple-600" size={16} />
          </div>
          <div>
            <div className="font-medium text-gray-900">Capture from Camera</div>
            <div className="text-sm text-gray-500">Photo of email or document</div>
          </div>
        </button>
      </div>
    </div>
  );
};
