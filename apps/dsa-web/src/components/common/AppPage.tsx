import type React from 'react';
import { cn } from '../../utils/cn';

interface AppPageProps {
  children: React.ReactNode;
  className?: string;
}

export const AppPage: React.FC<AppPageProps> = ({ children, className = '' }) => {
  return (
    <main className={cn('mx-auto h-full min-h-0 w-full max-w-7xl overflow-y-auto px-4 pb-8 pt-4 md:px-6 lg:px-8', className)}>
      {children}
    </main>
  );
};
