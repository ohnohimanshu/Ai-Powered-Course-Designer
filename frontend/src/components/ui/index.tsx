import React from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Loader2 } from 'lucide-react';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/* ─── Button ─── */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost';
    isLoading?: boolean;
    size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
    children, className, variant = 'primary', isLoading, size = 'md', ...props
}) => {
    const sizeClasses = {
        sm: 'px-4 py-2 text-sm',
        md: 'px-6 py-2.5',
        lg: 'px-8 py-3.5 text-lg',
    };

    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            className={cn(
                'inline-flex items-center justify-center gap-2 font-semibold disabled:opacity-40 disabled:pointer-events-none',
                variant === 'primary' && 'btn-primary',
                variant === 'secondary' && 'btn-secondary',
                variant === 'ghost' && 'btn-ghost',
                sizeClasses[size],
                className
            )}
            disabled={isLoading || props.disabled}
            {...props}
        >
            {isLoading ? (
                <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing...</span>
                </>
            ) : children}
        </motion.button>
    );
};

/* ─── Input ─── */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    icon?: React.ReactNode;
    error?: string;
}

export const Input: React.FC<InputProps> = ({ label, icon, error, className, ...props }) => {
    return (
        <div className="space-y-2">
            {label && (
                <label className="text-sm font-medium text-white/50 ml-0.5 tracking-wide">
                    {label}
                </label>
            )}
            <div className="relative">
                {icon && (
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20">
                        {icon}
                    </div>
                )}
                <input
                    className={cn(
                        'input-field',
                        icon && 'pl-11',
                        error && 'border-danger/50 focus:border-danger/70',
                        className
                    )}
                    {...props}
                />
            </div>
            {error && (
                <p className="text-xs text-danger ml-1">{error}</p>
            )}
        </div>
    );
};

/* ─── Card ─── */
interface CardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    animate?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className, hover = false, animate = true }) => {
    const Wrapper = animate ? motion.div : 'div';
    const animProps = animate ? {
        initial: { opacity: 0, y: 16 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] },
    } : {};

    return (
        <Wrapper
            {...animProps}
            className={cn(
                'glass-card p-6',
                hover && 'glass-card-hover cursor-pointer',
                className
            )}
        >
            {children}
        </Wrapper>
    );
};

/* ─── Badge ─── */
interface BadgeProps {
    children: React.ReactNode;
    variant?: 'primary' | 'success' | 'warning' | 'neutral';
    className?: string;
    icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'primary', icon, className }) => {
    const variantClasses = {
        primary: 'badge-primary',
        success: 'badge-success',
        warning: 'badge-warning',
        neutral: 'badge bg-white/5 text-white/50 border border-white/10',
    };

    return (
        <span className={cn(variantClasses[variant], className)}>
            {icon}
            {children}
        </span>
    );
};

/* ─── Skeleton ─── */
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
    <div className={cn('rounded-xl shimmer', className)} />
);
