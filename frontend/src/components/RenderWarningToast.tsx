'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, X } from 'lucide-react';

export function RenderWarningToast() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Show the toast after a short delay so it pops in
    const timer = setTimeout(() => setIsVisible(true), 1500);
    return () => clearTimeout(timer);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-right-8 fade-in duration-500 max-w-sm">
      <div className="bg-black border border-neutral-800 p-4 relative shadow-2xl overflow-hidden before:absolute before:left-0 before:top-0 before:w-1 before:h-full before:bg-yellow-500/50">
        <button 
          onClick={() => setIsVisible(false)}
          className="absolute top-2 right-2 text-neutral-500 hover:text-white transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
        
        <div className="flex gap-3 items-start pr-4">
          <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1">
            <h3 className="text-sm font-semibold tracking-wide text-neutral-200">
              TEST ENVIRONMENT NOTICE
            </h3>
            <p className="text-xs text-neutral-400 leading-relaxed">
              This application is hosted on Render's free tier. 
              The SQLite database is <strong>ephemeral</strong> and will be erased whenever the server spins down.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
