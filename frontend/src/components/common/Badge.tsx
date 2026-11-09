import React from 'react';

interface BadgeProps {
  variant?: 'verified' | 'needs_review' | 'conflicting' | 'unverified' | 'completed' | 'in_progress' | 'pending' | 'blocked' | 'critical' | 'high' | 'medium' | 'low' | 'approved' | 'rejected' | 'draft' | 'default';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, className = '' }) => {
  const getStyles = () => {
    switch (variant) {
      case 'verified':
      case 'completed':
      case 'approved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'needs_review':
      case 'pending':
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'in_progress':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200';
      case 'conflicting':
      case 'critical':
      case 'rejected':
      case 'blocked':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'high':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'low':
      case 'unverified':
      case 'draft':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getStyles()} ${className}`}
    >
      {children}
    </span>
  );
};

