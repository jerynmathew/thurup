import React from 'react';

interface LoadingProps {
    text?: string;
}

export const Loading: React.FC<LoadingProps> = ({ text = 'Loading...' }) => {
    return (
        <div className="flex flex-col items-center justify-center gap-4">
            <div className="w-12 h-12 border-4 border-neon-cyan border-t-transparent rounded-full animate-spin"></div>
            <p className="text-neon-cyan font-semibold animate-pulse">{text}</p>
        </div>
    );
};
