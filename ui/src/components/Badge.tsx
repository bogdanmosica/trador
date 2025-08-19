import React from 'react';

interface BadgeProps {
  variant: 'buy' | 'sell' | 'short' | 'long' | 'open' | 'closed' | 'status' | 'info';
  children?: React.ReactNode;
  icon?: string;
  className?: string;
}

const Badge: React.FC<BadgeProps> = ({ variant, children, icon, className = '' }) => {
  const getVariantClasses = (variant: string) => {
    switch (variant) {
      case 'buy':
      case 'long':
        return 'bg-green-100 text-green-800';
      case 'sell':
      case 'short':
        return 'bg-red-100 text-red-800';
      case 'open':
        return 'bg-green-100 text-green-800';
      case 'closed':
        return 'bg-red-100 text-red-800';
      case 'status':
        return 'bg-blue-100 text-blue-800';
      case 'info':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const baseClasses = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium';
  const variantClasses = getVariantClasses(variant);
  
  return (
    <span className={`${baseClasses} ${variantClasses} ${className}`}>
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </span>
  );
};

export default Badge;