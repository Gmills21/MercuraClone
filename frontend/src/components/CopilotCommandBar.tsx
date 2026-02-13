import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Command, ArrowRight, X, Loader2, TrendingUp, Repeat, History, Lightbulb, Check, AlertCircle } from 'lucide-react';
import { copilotApi } from '../services/api';
import { trackEvent } from '../posthog';

interface CopilotCommandBarProps {
  quoteId?: string;
  onApplyChange?: (change: any) => void;
  onClose?: () => void;
  className?: string;
}

interface CommandSuggestion {
  command: string;
  description: string;
  icon: string;
}

interface CommandResult {
  success: boolean;
  action?: string;
  message: string;
  changes?: any;
  alternatives?: any[];
  optimizations?: any[];
  similar_quotes?: any[];
  confidence?: number;
}

export const CopilotCommandBar: React.FC<CopilotCommandBarProps> = ({
  quoteId,
  onApplyChange,
  onClose,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<CommandResult | null>(null);
  const [suggestions, setSuggestions] = useState<CommandSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load suggestions when quote changes
  useEffect(() => {
    if (quoteId) {
      loadSuggestions();
    }
  }, [quoteId]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        if (!result) {
          setIsOpen(false);
          onClose?.();
        }
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, result, onClose]);

  // Keyboard shortcut: Cmd/Ctrl + K to open
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
        setResult(null);
      }
      if (e.key === 'Escape') {
        if (result) {
          setResult(null);
        } else {
          setIsOpen(false);
          onClose?.();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, result]);

  const loadSuggestions = async () => {
    if (!quoteId) return;
    try {
      const res = await copilotApi.getSuggestions(quoteId);
      setSuggestions(res.data.suggestions || []);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isProcessing) return;

    setIsProcessing(true);
    setShowSuggestions(false);

    try {
      const res = await copilotApi.command(input.trim(), quoteId);
      setResult(res.data);

      // Track successful command
      trackEvent('copilot_command_used', {
        command: input.trim(),
        action: res.data.action,
        success: res.data.success,
        quote_id: quoteId
      });

      // Add to recent commands
      setRecentCommands(prev => [input.trim(), ...prev.slice(0, 4)]);
    } catch (error) {
      console.error('Copilot command failed:', error);
      setResult({
        success: false,
        message: 'Something went wrong. Please try again.'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSuggestionClick = (suggestion: CommandSuggestion) => {
    setInput(suggestion.command);
    handleSubmit();
  };

  const handleApplyChange = () => {
    if (result?.changes && onApplyChange) {
      onApplyChange(result.changes);
      setResult(null);
      setInput('');
      setShowSuggestions(true);

      trackEvent('copilot_change_applied', {
        action: result.action,
        quote_id: quoteId
      });
    }
  };

  const handleReset = () => {
    setResult(null);
    setInput('');
    setShowSuggestions(true);
    inputRef.current?.focus();
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'trending-up': return <TrendingUp size={16} />;
      case 'link': return <Check size={16} />;
      case 'history': return <History size={16} />;
      case 'repeat': return <Repeat size={16} />;
      default: return <Lightbulb size={16} />;
    }
  };

  // If closed, show the trigger button
  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`inline-flex items-center gap-2 px-4 py-2 bg-slate-900/80 hover:bg-slate-800 text-slate-300 rounded-lg border border-slate-700/50 transition-all hover:scale-[1.02] ${className}`}
      >
        <Sparkles size={16} className="text-orange-400" />
        <span className="text-sm font-medium">AI Copilot</span>
        <kbd className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 text-xs bg-slate-800 rounded border border-slate-700 text-slate-500">
          <Command size={10} /> K
        </kbd>
      </button>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`relative z-50 ${className}`}
    >
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={() => !result && setIsOpen(false)} />

      {/* Command Bar Container */}
      <div className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-2xl px-4">
        <div className="bg-slate-900 rounded-2xl shadow-2xl border border-slate-700/50 overflow-hidden animate-in fade-in slide-in-from-top-4 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
                <Sparkles size={16} className="text-white" />
              </div>
              <span className="font-semibold text-slate-200">AI Copilot</span>
              <span className="text-xs text-slate-500 px-2 py-0.5 bg-slate-800 rounded-full">Beta</span>
            </div>
            <button
              onClick={() => { setIsOpen(false); onClose?.(); }}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="p-4">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  setShowSuggestions(true);
                }}
                placeholder="What would you like to do? Try 'Change item 1 to stainless steel'..."
                className="w-full px-4 py-3 pl-12 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/50 focus:border-orange-500/50 transition-all"
                disabled={isProcessing || !!result}
              />
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">
                {isProcessing ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Command size={18} />
                )}
              </div>
              {input && !result && (
                <button
                  type="submit"
                  disabled={isProcessing}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 bg-orange-500 hover:bg-orange-400 disabled:opacity-50 text-white rounded-lg transition-colors"
                >
                  <ArrowRight size={16} />
                </button>
              )}
            </div>
          </form>

          {/* Result Display */}
          {result && (
            <div className="px-4 pb-4 animate-in fade-in slide-in-from-bottom-2 duration-200">
              <div className={`p-4 rounded-xl border ${result.success ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                <div className="flex items-start gap-3">
                  {result.success ? (
                    <div className="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Check size={16} className="text-emerald-400" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-red-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                      <AlertCircle size={16} className="text-red-400" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm ${result.success ? 'text-emerald-200' : 'text-red-200'}`}>
                      {result.message}
                    </p>

                    {/* Show alternatives if available */}
                    {result.alternatives && result.alternatives.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs text-slate-400 uppercase font-semibold">Alternatives</p>
                        {result.alternatives.map((alt, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-2 bg-slate-900 rounded-lg border border-slate-800"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono text-slate-500">{alt.sku}</span>
                              <span className="text-sm text-slate-300 truncate max-w-[200px]">{alt.name}</span>
                            </div>
                            <span className="text-xs text-emerald-400 font-medium">
                              +{alt.margin_potential?.toFixed(1)}% margin
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Show optimizations if available */}
                    {result.optimizations && result.optimizations.length > 0 && (
                      <div className="mt-3 space-y-2">
                        <p className="text-xs text-slate-400 uppercase font-semibold">
                          Potential Profit Increase: ${result.potential_profit_increase?.toFixed(2)}
                        </p>
                        {result.optimizations.slice(0, 3).map((opt, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-2 bg-slate-900 rounded-lg border border-slate-800"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-slate-300">Item {opt.item_index + 1}</span>
                              <ArrowRight size={12} className="text-slate-500" />
                              <span className="text-sm text-emerald-400 truncate max-w-[150px]">
                                {opt.alternative.name}
                              </span>
                            </div>
                            <span className="text-xs text-emerald-400 font-medium">
                              +${opt.potential_profit_increase?.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 mt-4">
                      {result.success && result.changes && (
                        <button
                          onClick={handleApplyChange}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                        >
                          <Check size={14} />
                          Apply Change
                        </button>
                      )}
                      <button
                        onClick={handleReset}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg transition-colors"
                      >
                        Try Another
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Suggestions */}
          {!result && showSuggestions && (
            <div className="px-4 pb-4">
              {/* Context-aware suggestions */}
              {suggestions.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-slate-500 uppercase font-semibold mb-2 px-1">Suggestions for this quote</p>
                  <div className="space-y-1">
                    {suggestions.map((suggestion, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-slate-800 rounded-lg transition-colors group"
                      >
                        <div className="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-lg flex items-center justify-center text-slate-400 group-hover:text-slate-300 transition-colors">
                          {getIcon(suggestion.icon)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-300 font-medium truncate">{suggestion.command}</p>
                          <p className="text-xs text-slate-500 truncate">{suggestion.description}</p>
                        </div>
                        <ArrowRight size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Quick commands */}
              <div>
                <p className="text-xs text-slate-500 uppercase font-semibold mb-2 px-1">Quick commands</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    'Change item 1 to...',
                    'Find alternatives',
                    'Show similar quotes',
                    'Optimize margins'
                  ].map((cmd, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setInput(cmd);
                        inputRef.current?.focus();
                      }}
                      className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-300 rounded-lg transition-colors"
                    >
                      {cmd}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="px-4 py-2 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <span>Natural language commands supported</span>
            <div className="flex items-center gap-3">
              <span className="hidden sm:inline"><kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">Enter</kbd> to execute</span>
              <span className="hidden sm:inline"><kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700">Esc</kbd> to close</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CopilotCommandBar;
