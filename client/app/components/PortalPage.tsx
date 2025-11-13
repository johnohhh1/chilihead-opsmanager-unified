'use client';

import { useState, useEffect } from 'react';

interface MetricData {
  comp_sales_day: number | null;
  comp_sales_ptd: number | null;
  comp_sales_vs_plan_ptd: number | null;
  dine_in_gwap_day: number | null;
  dine_in_gwap_ltd: number | null;
  dine_in_gwap_r4w: number | null;
  to_go_gwap_day: number | null;
  to_go_gwap_ltd: number | null;
  to_go_gwap_r4w: number | null;
  labor_percent: number | null;
  guest_satisfaction: number | null;
  food_cost: number | null;
  speed_of_service: number | null;
}

interface PortalData {
  success: boolean;
  email_date?: string;
  extracted_at?: string;
  metrics?: MetricData;
  error?: string;
}

interface MetricCardProps {
  label: string;
  value: number | null;
  unit?: string;
  isPercentage?: boolean;
  size?: 'small' | 'medium' | 'large';
}

function MetricCard({ label, value, unit = '', isPercentage = false, size = 'medium' }: MetricCardProps) {
  const displayValue = value !== null ? (isPercentage ? `${value}%` : `${value}${unit}`) : 'N/A';
  const isNegative = value !== null && value < 0;
  const isPositive = value !== null && value > 0;

  const sizeClasses = {
    small: 'p-3',
    medium: 'p-4',
    large: 'p-6'
  };

  const textSizeClasses = {
    small: 'text-xl',
    medium: 'text-2xl',
    large: 'text-3xl'
  };

  return (
    <div className={`bg-gray-800 rounded-lg border border-gray-700 ${sizeClasses[size]} shadow-lg`}>
      <div className="text-gray-400 text-sm font-medium mb-2">{label}</div>
      <div
        className={`${textSizeClasses[size]} font-bold ${
          isNegative ? 'text-red-400' : isPositive ? 'text-green-400' : 'text-white'
        }`}
      >
        {displayValue}
      </div>
    </div>
  );
}

export default function PortalPage() {
  const [portalData, setPortalData] = useState<PortalData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await fetch('/api/backend/portal-dashboard');
      const data = await response.json();

      if (data.success) {
        setPortalData(data);
      } else {
        setError(data.error || 'Failed to extract metrics');
      }
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError('Failed to load portal dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-white">📊 RAP Mobile Dashboard</h1>
          <p className="text-gray-300 mt-2">Restaurant Analytics Portal - Chili's #605</p>
          {portalData?.extracted_at && (
            <p className="text-sm text-gray-400 mt-1">
              Last updated: {new Date(portalData.extracted_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto p-6">
        {/* Refresh Button */}
        <div className="mb-6 flex justify-end">
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2 font-semibold"
          >
            <svg
              className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {loading ? 'Extracting Metrics...' : 'Refresh Metrics'}
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-400">Extracting metrics from RAP Mobile email...</p>
            </div>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-900/20 border border-red-600 rounded-lg p-6 text-center">
            <p className="text-red-400 text-lg">{error}</p>
            <button
              onClick={fetchMetrics}
              className="mt-4 px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {portalData?.metrics && !loading && (
          <div className="space-y-6">
            {/* Sales Section */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-red-500">💰</span> Sales Performance
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  label="Comp Sales Day"
                  value={portalData.metrics.comp_sales_day}
                  isPercentage
                  size="large"
                />
                <MetricCard
                  label="Comp Sales PTD"
                  value={portalData.metrics.comp_sales_ptd}
                  isPercentage
                  size="large"
                />
                <MetricCard
                  label="Comp Sales vs Plan PTD"
                  value={portalData.metrics.comp_sales_vs_plan_ptd}
                  isPercentage
                  size="large"
                />
              </div>
            </div>

            {/* Dine In GWAP Section */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-blue-400">🍽️</span> Dine In GWAP (Guest With Average Party)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard label="Day" value={portalData.metrics.dine_in_gwap_day} isPercentage />
                <MetricCard label="LTD (Life-to-Date)" value={portalData.metrics.dine_in_gwap_ltd} isPercentage />
                <MetricCard label="R4W (Rolling 4 Weeks)" value={portalData.metrics.dine_in_gwap_r4w} isPercentage />
              </div>
            </div>

            {/* To Go GWAP Section */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-yellow-400">🥡</span> To Go GWAP
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard label="Day" value={portalData.metrics.to_go_gwap_day} isPercentage />
                <MetricCard label="LTD (Life-to-Date)" value={portalData.metrics.to_go_gwap_ltd} isPercentage />
                <MetricCard label="R4W (Rolling 4 Weeks)" value={portalData.metrics.to_go_gwap_r4w} isPercentage />
              </div>
            </div>

            {/* Operations Metrics */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-green-400">📈</span> Operations Metrics
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard label="Labor %" value={portalData.metrics.labor_percent} isPercentage />
                <MetricCard label="Guest Satisfaction" value={portalData.metrics.guest_satisfaction} unit="/100" />
                <MetricCard label="Food Cost %" value={portalData.metrics.food_cost} isPercentage />
                <MetricCard label="Speed of Service" value={portalData.metrics.speed_of_service} unit=" min" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
          <p className="text-sm text-gray-400">
            <span className="font-semibold text-gray-300">Note:</span> Metrics are automatically extracted from your
            daily RAP Mobile email using AI vision. Click "Refresh Metrics" to pull the latest data.
          </p>
        </div>
      </div>
    </div>
  );
}
