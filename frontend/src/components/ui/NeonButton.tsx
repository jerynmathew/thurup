import React from 'react';

interface NeonButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'cyan' | 'magenta' | 'amber' | 'primary' | 'secondary' | 'danger';
    glow?: boolean;
}

export const NeonButton: React.FC<NeonButtonProps> = ({
    children,
    variant = 'cyan',
    glow = false,
    className = '',
    disabled,
    ...props
}) => {
    const getVariantStyles = () => {
        switch (variant) {
            case 'cyan':
                return 'bg-gradient-to-r from-neon-cyan to-blue-600 text-white shadow-cyan-500/20';
            case 'magenta':
                return 'bg-gradient-to-r from-neon-magenta to-purple-600 text-white shadow-magenta-500/20';
            case 'amber':
                return 'bg-gradient-to-r from-neon-amber to-orange-600 text-white shadow-amber-500/20';
            case 'primary':
                return 'bg-primary-600 hover:bg-primary-700 text-white';
            case 'secondary':
                return 'bg-slate-700 hover:bg-slate-600 text-white';
            case 'danger':
                return 'bg-red-600 hover:bg-red-700 text-white';
            default:
                return 'bg-slate-700 text-white';
        }
    };

    const glowStyle = glow ? `shadow-[0_0_15px_rgba(var(--color-${variant}),0.5)]` : '';
    const disabledStyle = disabled ? 'opacity-50 cursor-not-allowed grayscale' : 'hover:scale-105 active:scale-95';

    return (
        <button
            className={`
        px-6 py-2 rounded-full font-bold transition-all duration-200
        ${getVariantStyles()}
        ${glowStyle}
        ${disabledStyle}
        ${className}
      `}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
};
