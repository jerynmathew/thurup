/**
 * Main App component with React Router.
 */

import { RouterProvider } from 'react-router';
import { router } from './router';
import { useUIStore } from './stores';
import { ErrorBoundary } from './components/ErrorBoundary';

export default function App() {
  const toasts = useUIStore((state) => state.toasts);
  const removeToast = useUIStore((state) => state.removeToast);

  return (
    <ErrorBoundary>
      <RouterProvider router={router} />

      {/* Global Toast Container */}
      {toasts.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`px-4 py-3 rounded-lg shadow-lg backdrop-blur-sm border animate-slide-in ${
                toast.type === 'success'
                  ? 'bg-green-900/90 border-green-700 text-green-100'
                  : toast.type === 'error'
                  ? 'bg-red-900/90 border-red-700 text-red-100'
                  : toast.type === 'warning'
                  ? 'bg-yellow-900/90 border-yellow-700 text-yellow-100'
                  : 'bg-blue-900/90 border-blue-700 text-blue-100'
              }`}
            >
              <div className="flex items-center gap-2">
                <span>{toast.message}</span>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="ml-2 text-current opacity-70 hover:opacity-100 transition-opacity"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </ErrorBoundary>
  );
}
