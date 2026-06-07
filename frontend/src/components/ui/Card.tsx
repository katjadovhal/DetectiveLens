import type { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
  highlight?: boolean;
}

export function Card({ children, className = '', highlight = false }: CardProps) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-8 ${
        highlight ? 'bg-[var(--color-accent-yellow)]/30 border-2 border-[var(--color-accent-yellow)]' : 'bg-white border-2 border-gray-100 shadow-sm'
      } ${className}`}
    >
      {children}
    </div>
  );
}
