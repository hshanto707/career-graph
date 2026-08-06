import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/**
 * Last-resort safety net for render crashes React Query's per-hook error
 * handling can't catch (a bug in render logic, not a failed fetch) --
 * without this, such a crash unmounts the whole app to a blank white
 * screen with no recovery path. Deliberately outside AppLayout/AuthProvider
 * dependency: this must still render correctly if auth/layout state itself
 * is what crashed.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled render error:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ error: null });
    window.location.reload();
  };

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
          <div className="max-w-md w-full flex flex-col items-center text-center gap-4">
            <AlertTriangle className="h-10 w-10 text-destructive" />
            <div>
              <h1 className="text-lg font-semibold text-foreground">Something went wrong</h1>
              <p className="text-sm text-muted-foreground mt-1">
                An unexpected error occurred and this page couldn't continue. Reloading usually
                fixes it -- if it keeps happening, please let us know what you were doing.
              </p>
            </div>
            <Button onClick={this.handleReload}>Reload page</Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
