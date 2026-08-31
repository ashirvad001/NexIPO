import React, { Component, ErrorInfo, ReactNode } from 'react';
import ErrorComponent from './Error';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <ErrorComponent 
          message="Something went wrong. Please reload the page." 
          retry={this.handleReload} 
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
