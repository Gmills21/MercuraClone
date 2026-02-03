import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, XCircle, RefreshCw, Download, Upload, ArrowRight, Link2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export const QuickBooksIntegration = () => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const res = await api.get('/quickbooks/status');
      setStatus(res.data);
    } catch (err) {
      console.error('Failed to check status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const res = await api.get('/quickbooks/auth-url');
      if (res.data.auth_url) {
        // Open QuickBooks auth in popup or redirect
        window.location.href = res.data.auth_url;
      }
    } catch (err) {
      setError('Failed to get authorization URL');
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Disconnect QuickBooks? This will stop all syncing.')) return;
    
    try {
      await api.post('/quickbooks/disconnect');
      setStatus({ connected: false });
      setSyncResult(null);
    } catch (err) {
      setError('Failed to disconnect');
    }
  };

  const handleImport = async () => {
    setSyncing(true);
    setError(null);
    try {
      const res = await api.post('/quickbooks/sync/import');
      setSyncResult(res.data);
      checkStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Import failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleBidirectionalSync = async () => {
    setSyncing(true);
    setError(null);
    try {
      const res = await api.post('/quickbooks/sync/bidirectional');
      setSyncResult(res.data);
      checkStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="animate-spin text-orange-600" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">QuickBooks Integration</h1>
              <p className="text-gray-600 mt-1">Sync your products, customers, and quotes</p>
            </div>
            <Link to="/" className="text-gray-500 hover:text-gray-700">
              ← Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-8 py-8">
        {/* Connection Status */}
        <div className={`bg-white border rounded-lg p-6 mb-6 ${status?.connected ? 'border-green-200' : 'border-gray-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-lg ${status?.connected ? 'bg-green-50' : 'bg-gray-100'}`}>
                {status?.connected ? (
                  <CheckCircle className="text-green-600" size={24} />
                ) : (
                  <Link2 className="text-gray-400" size={24} />
                )}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {status?.connected ? 'Connected to QuickBooks' : 'Not Connected'}
                </h2>
                <p className="text-gray-600">
                  {status?.connected 
                    ? `Realm ID: ${status.realm_id} • Connected ${new Date(status.connected_at).toLocaleDateString()}`
                    : 'Connect your QuickBooks account to enable automatic syncing'
                  }
                </p>
              </div>
            </div>
            
            {status?.connected ? (
              <button
                onClick={handleDisconnect}
                className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
              >
                <XCircle size={18} />
                Disconnect
              </button>
            ) : (
              <button
                onClick={handleConnect}
                className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors"
              >
                <Link2 size={18} />
                Connect QuickBooks
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-center gap-3 text-red-700">
            <AlertCircle size={20} />
            {error}
          </div>
        )}

        {/* Sync Options */}
        {status?.connected && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Import from QB */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Download className="text-blue-600" size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Import from QuickBooks</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Pull your products and customers from QuickBooks into OpenMercura
                  </p>
                  <button
                    onClick={handleImport}
                    disabled={syncing}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {syncing ? <RefreshCw className="animate-spin" size={16} /> : <Download size={16} />}
                    Import Now
                  </button>
                </div>
              </div>
            </div>

            {/* Bidirectional Sync */}
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-50 rounded-lg">
                  <RefreshCw className="text-purple-600" size={24} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">Magic Sync</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Two-way sync: Import from QB + Export new items to QB
                  </p>
                  <button
                    onClick={handleBidirectionalSync}
                    disabled={syncing}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {syncing ? <RefreshCw className="animate-spin" size={16} /> : <RefreshCw size={16} />}
                    Sync Both Ways
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sync Results */}
        {syncResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-3 text-green-800 mb-4">
              <CheckCircle size={24} />
              <h3 className="font-semibold">Sync Complete!</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              {syncResult.imported && (
                <>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-900">{syncResult.imported.products}</div>
                    <div className="text-sm text-gray-600">Products Imported</div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-900">{syncResult.imported.customers}</div>
                    <div className="text-sm text-gray-600">Customers Imported</div>
                  </div>
                </>
              )}
              
              {syncResult.created !== undefined && (
                <>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-900">{syncResult.created}</div>
                    <div className="text-sm text-gray-600">Items Created in QB</div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-2xl font-bold text-gray-900">{syncResult.errors || 0}</div>
                    <div className="text-sm text-gray-600">Errors</div>
                  </div>
                </>
              )}
            </div>
            
            <p className="mt-4 text-green-700">{syncResult.message}</p>
          </div>
        )}

        {/* Benefits Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-4">What Gets Synced</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex gap-3">
              <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <h4 className="font-medium text-gray-900">Products</h4>
                <p className="text-sm text-gray-600">Names, SKUs, prices, descriptions</p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <h4 className="font-medium text-gray-900">Customers</h4>
                <p className="text-sm text-gray-600">Names, emails, phone numbers, companies</p>
              </div>
            </div>
            
            <div className="flex gap-3">
              <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
              <div>
                <h4 className="font-medium text-gray-900">Quotes</h4>
                <p className="text-sm text-gray-600">Export as Estimates in QuickBooks</p>
              </div>
            </div>
          </div>
        </div>

        {/* How It Works */}
        {!status?.connected && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-blue-900 mb-4">How It Works</h3>
            <ol className="space-y-3 text-blue-800">
              <li className="flex items-start gap-3">
                <span className="font-bold">1.</span>
                Click "Connect QuickBooks" above
              </li>
              <li className="flex items-start gap-3">
                <span className="font-bold">2.</span>
                Sign in to your QuickBooks account
              </li>
              <li className="flex items-start gap-3">
                <span className="font-bold">3.</span>
                Click "Import" to pull your products and customers
              </li>
              <li className="flex items-start gap-3">
                <span className="font-bold">4.</span>
                Start creating quotes with your QB data!
              </li>
            </ol>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuickBooksIntegration;
