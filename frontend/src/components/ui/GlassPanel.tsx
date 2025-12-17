import React from 'react';

interface GlassPanelProps {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
}

export const GlassPanel: React.FC<GlassPanelProps> = ({ children, className = '', onClick }) => {
    return (
        <div
            className={`glass rounded-xl border border-white/5 shadow-lg backdrop-blur-md ${className}`}
            onClick={onClick}
        >
            {children}
        </div>
    );
};
