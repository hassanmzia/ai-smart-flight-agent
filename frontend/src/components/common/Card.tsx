import { HTMLAttributes } from 'react';
import { cn } from '@/utils/helpers';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  variant?: 'default' | 'glass' | 'gradient';
}

export const Card = ({
  children,
  className,
  hover = false,
  padding = 'md',
  variant = 'default',
  ...props
}: CardProps) => {
  const paddingStyles = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const variants = {
    default:
      'bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl border border-gray-200/60 dark:border-gray-700/50 shadow-lg shadow-gray-200/40 dark:shadow-gray-900/30',
    glass:
      'bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl rounded-2xl border border-white/40 dark:border-gray-600/30 shadow-xl shadow-gray-200/30 dark:shadow-gray-900/40',
    gradient:
      'bg-gradient-to-br from-white via-white to-gray-50 dark:from-gray-800 dark:via-gray-800 dark:to-gray-900 rounded-2xl border border-gray-200/60 dark:border-gray-700/50 shadow-lg shadow-gray-200/40 dark:shadow-gray-900/30',
  };

  return (
    <div
      className={cn(
        variants[variant],
        hover && 'hover:shadow-xl hover:shadow-gray-200/50 dark:hover:shadow-gray-900/40 hover:border-primary-200 dark:hover:border-primary-800/50 transition-all duration-300 cursor-pointer transform hover:-translate-y-1',
        paddingStyles[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={cn('mb-4', className)} {...props}>
      {children}
    </div>
  );
};

export const CardTitle = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) => {
  return (
    <h3
      className={cn('text-xl font-bold text-gray-900 dark:text-white', className)}
      {...props}
    >
      {children}
    </h3>
  );
};

export const CardContent = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={cn('text-gray-600 dark:text-gray-300', className)} {...props}>
      {children}
    </div>
  );
};

export const CardFooter = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div className={cn('mt-4 pt-4 border-t border-gray-200/60 dark:border-gray-700/50', className)} {...props}>
      {children}
    </div>
  );
};

export default Card;
