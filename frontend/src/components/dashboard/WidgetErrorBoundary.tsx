import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class WidgetErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Widget caught render error:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex flex-col justify-center items-center p-6 rounded-2xl bg-slate-900/80 border border-rose-500/30 text-center shadow-xl">
          <AlertCircle className="w-8 h-8 text-rose-400 mb-2" />
          <h3 className="text-sm font-bold text-white mb-1">
            {this.props.fallbackTitle || 'Widget Render Error'}
          </h3>
          <p className="text-xs text-rose-300/80 max-w-xs mb-4">
            An unexpected error occurred while rendering this widget.
          </p>
          <button
            onClick={this.handleRetry}
            className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 border border-rose-500/30 text-xs font-medium transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
