import { Component, ErrorInfo, ReactNode } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error boundary component to catch and handle React errors gracefully.
 *
 * Wraps components to prevent entire app crashes when errors occur.
 * Provides user-friendly error UI with recovery options.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you would send this to an error reporting service
    // Example: Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <Card className="max-w-2xl w-full">
            <div className="text-center space-y-4">
              <div className="text-6xl">⚠️</div>
              <h1 className="text-2xl font-bold text-gray-900">
                Something went wrong
              </h1>
              <p className="text-gray-600">
                We're sorry, but something unexpected happened. The error has been logged.
              </p>

              {import.meta.env.DEV && this.state.error && (
                <div className="mt-6 text-left">
                  <details className="bg-gray-100 rounded-lg p-4">
                    <summary className="cursor-pointer font-semibold text-gray-700 mb-2">
                      Error Details (Development Only)
                    </summary>
                    <div className="space-y-2">
                      <div>
                        <p className="font-mono text-sm text-red-600">
                          {this.state.error.name}: {this.state.error.message}
                        </p>
                      </div>
                      {this.state.error.stack && (
                        <div>
                          <p className="text-xs font-semibold text-gray-700 mb-1">
                            Stack Trace:
                          </p>
                          <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                            {this.state.error.stack}
                          </pre>
                        </div>
                      )}
                      {this.state.errorInfo?.componentStack && (
                        <div>
                          <p className="text-xs font-semibold text-gray-700 mb-1">
                            Component Stack:
                          </p>
                          <pre className="text-xs text-gray-600 overflow-x-auto whitespace-pre-wrap">
                            {this.state.errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}

              <div className="flex gap-3 justify-center mt-6">
                <Button onClick={this.handleReset} variant="secondary">
                  Try Again
                </Button>
                <Button onClick={this.handleReload} variant="primary">
                  Reload Page
                </Button>
              </div>

              <p className="text-sm text-gray-500 mt-4">
                If this problem persists, please contact support.
              </p>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
