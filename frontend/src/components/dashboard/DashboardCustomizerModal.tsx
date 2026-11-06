import React, { useState, useEffect, useRef } from 'react';
import {
  DashboardWidgetConfig,
  WidgetSize,
} from '../../types/dashboard';
import { getWidgetDefinition } from './registry';
import {
  X,
  ChevronUp,
  ChevronDown,
  Eye,
  EyeOff,
  RotateCcw,
  Save,
  Sliders,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

interface DashboardCustomizerModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentWidgets: DashboardWidgetConfig[];
  onSave: (updatedWidgets: DashboardWidgetConfig[]) => Promise<void>;
  onReset: () => Promise<void>;
  isSaving: boolean;
  saveError: string | null;
}

export const DashboardCustomizerModal: React.FC<DashboardCustomizerModalProps> = ({
  isOpen,
  onClose,
  currentWidgets,
  onSave,
  onReset,
  isSaving,
  saveError,
}) => {
  // Local working copy of widget configurations
  const [draftWidgets, setDraftWidgets] = useState<DashboardWidgetConfig[]>(() =>
    [...currentWidgets].sort((a, b) => a.order - b.order)
  );

  const modalRef = useRef<HTMLDivElement>(null);

  // Sync draft whenever modal is opened
  useEffect(() => {
    if (isOpen) {
      setDraftWidgets([...currentWidgets].sort((a, b) => a.order - b.order));
    }
  }, [isOpen, currentWidgets]);

  // Handle Escape key and focus trap
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSaving) {
        onClose();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // Initial focus on modal close button or container
    const timer = setTimeout(() => {
      const focusable = modalRef.current?.querySelector<HTMLElement>(
        'button:not([disabled])'
      );
      focusable?.focus();
    }, 50);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timer);
    };
  }, [isOpen, isSaving, onClose]);

  if (!isOpen) return null;

  const handleToggleVisibility = (widgetId: string) => {
    setDraftWidgets((prev) =>
      prev.map((w) =>
        w.widget_id === widgetId ? { ...w, is_visible: !w.is_visible } : w
      )
    );
  };

  const handleChangeSize = (widgetId: string, size: WidgetSize) => {
    setDraftWidgets((prev) =>
      prev.map((w) => (w.widget_id === widgetId ? { ...w, size } : w))
    );
  };

  const handleMoveUp = (index: number) => {
    if (index <= 0) return;
    setDraftWidgets((prev) => {
      const copy = [...prev];
      const target = copy[index];
      const previous = copy[index - 1];

      // Swap positions and normalize orders
      copy[index - 1] = target;
      copy[index] = previous;

      return copy.map((w, idx) => ({ ...w, order: idx }));
    });
  };

  const handleMoveDown = (index: number) => {
    if (index >= draftWidgets.length - 1) return;
    setDraftWidgets((prev) => {
      const copy = [...prev];
      const target = copy[index];
      const next = copy[index + 1];

      // Swap positions and normalize orders
      copy[index + 1] = target;
      copy[index] = next;

      return copy.map((w, idx) => ({ ...w, order: idx }));
    });
  };

  const handleSave = async () => {
    // Ensure orders are sequential integers 0..n-1 before saving
    const normalized = draftWidgets.map((w, idx) => ({
      ...w,
      order: idx,
    }));
    await onSave(normalized);
  };

  return (
    <div
      ref={modalRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="customizer-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
    >
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <h2
                id="customizer-modal-title"
                className="text-base font-bold text-white tracking-tight"
              >
                Customize Dashboard
              </h2>
              <p className="text-xs text-slate-400">
                Reorder, resize, and choose which widgets appear
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={isSaving}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition disabled:opacity-50"
            aria-label="Close customizer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {saveError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{saveError}</span>
            </div>
          )}

          <div className="text-xs text-slate-400 mb-2">
            Order widgets from top to bottom. Disabled widgets remain saved in your preferences.
          </div>

          <div className="space-y-2">
            {draftWidgets.map((widget, index) => {
              const def = getWidgetDefinition(widget.widget_id);
              const title = def?.title || widget.widget_id;
              const isFirst = index === 0;
              const isLast = index === draftWidgets.length - 1;

              return (
                <div
                  key={widget.widget_id}
                  className={`flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl border transition gap-3 ${
                    widget.is_visible
                      ? 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                      : 'bg-slate-950/20 border-slate-800/40 opacity-60'
                  }`}
                >
                  {/* Left: Reorder Controls & Title */}
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="flex flex-col gap-0.5 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleMoveUp(index)}
                        disabled={isFirst || isSaving}
                        className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 disabled:opacity-30 disabled:hover:bg-slate-800/80 transition"
                        title="Move Up"
                        aria-label={`Move ${title} Up`}
                      >
                        <ChevronUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMoveDown(index)}
                        disabled={isLast || isSaving}
                        className="p-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 disabled:opacity-30 disabled:hover:bg-slate-800/80 transition"
                        title="Move Down"
                        aria-label={`Move ${title} Down`}
                      >
                        <ChevronDown className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-white truncate flex items-center gap-2">
                        <span>{title}</span>
                        {!widget.is_visible && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            Hidden
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-500 truncate mt-0.5">
                        {def?.description}
                      </div>
                    </div>
                  </div>

                  {/* Right: Size selector and Visibility toggle */}
                  <div className="flex items-center justify-between sm:justify-end gap-2 shrink-0">
                    {/* Size Selector */}
                    <div className="flex items-center rounded-lg bg-slate-900 border border-slate-800 p-0.5">
                      {(['small', 'medium', 'full'] as WidgetSize[]).map((size) => (
                        <button
                          key={size}
                          type="button"
                          onClick={() => handleChangeSize(widget.widget_id, size)}
                          disabled={!widget.is_visible || isSaving}
                          className={`px-2 py-0.5 text-[10px] font-medium rounded-md capitalize transition ${
                            widget.size === size
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                              : 'text-slate-400 hover:text-white'
                          } disabled:opacity-40`}
                        >
                          {size}
                        </button>
                      ))}
                    </div>

                    {/* Visibility Toggle */}
                    <button
                      type="button"
                      onClick={() => handleToggleVisibility(widget.widget_id)}
                      disabled={isSaving}
                      className={`p-1.5 rounded-lg border text-xs font-medium transition flex items-center gap-1.5 ${
                        widget.is_visible
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
                          : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
                      }`}
                      title={widget.is_visible ? 'Hide Widget' : 'Show Widget'}
                      aria-label={widget.is_visible ? `Hide ${title}` : `Show ${title}`}
                    >
                      {widget.is_visible ? (
                        <>
                          <Eye className="w-3.5 h-3.5" />
                          <span className="text-[11px] hidden sm:inline">Visible</span>
                        </>
                      ) : (
                        <>
                          <EyeOff className="w-3.5 h-3.5" />
                          <span className="text-[11px] hidden sm:inline">Hidden</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            type="button"
            onClick={onReset}
            disabled={isSaving}
            className="w-full sm:w-auto px-3 py-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 text-xs font-medium transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Restore Defaults</span>
          </button>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="flex-1 sm:flex-initial px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-medium transition disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 sm:flex-initial px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition flex items-center justify-center gap-1.5 disabled:opacity-50 shadow-lg shadow-emerald-500/20"
            >
              {isSaving ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="w-3.5 h-3.5" />
                  <span>Save Layout</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

