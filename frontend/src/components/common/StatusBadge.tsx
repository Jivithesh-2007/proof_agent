import React from 'react';
import { AnalysisStatus } from '../../types';
import { CheckCircle2, AlertTriangle, XCircle, Clock } from 'lucide-react';
import { cn } from '../../lib/utils';

interface StatusBadgeProps {
  status: AnalysisStatus;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md', className }) => {
  const config: Record<AnalysisStatus, { label: string; icon: React.ComponentType<{ className?: string }>; styles: string }> = {
    verified: {
      label: 'Verified',
      icon: CheckCircle2,
      styles: 'bg-[#E64A32]/20 text-[#E64A32] border-[#E64A32]/40',
    },
    warning: {
      label: 'Warning',
      icon: AlertTriangle,
      styles: 'bg-[#E18230]/20 text-[#E18230] border-[#E18230]/40',
    },
    refused: {
      label: 'Refused',
      icon: XCircle,
      styles: 'bg-[#E64A32]/30 text-[#F4F5EC] border-[#E64A32]',
    },
    failed: {
      label: 'Failed',
      icon: XCircle,
      styles: 'bg-rose-950/60 text-rose-400 border-rose-500/30',
    },
    processing: {
      label: 'Processing',
      icon: Clock,
      styles: 'bg-[#E18230]/20 text-[#E18230] border-[#E18230]/30 animate-pulse',
    },
    document_supported: {
      label: 'Document Supported',
      icon: CheckCircle2,
      styles: 'bg-blue-950/60 text-blue-400 border-blue-500/30',
    },
    model_prediction: {
      label: 'Model Prediction',
      icon: AlertTriangle,
      styles: 'bg-purple-950/60 text-purple-400 border-purple-500/30',
    },
  };

  const current = config[status] || {
    label: status,
    icon: AlertTriangle,
    styles: 'bg-[#3C3B39] text-[#F4F5EC] border-[#3C3B39]',
  };

  const Icon = current.icon;

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    md: 'px-2.5 py-1 text-xs gap-1.5',
    lg: 'px-3 py-1.5 text-sm gap-2 font-semibold',
  }[size];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border font-medium tracking-wide transition-colors',
        current.styles,
        sizeStyles,
        className
      )}
    >
      <Icon className={cn(size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5')} />
      {current.label}
    </span>
  );
};
