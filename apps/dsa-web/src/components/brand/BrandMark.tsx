import type React from 'react';
import { APP_BRAND } from '../../config/brand';
import { cn } from '../../utils/cn';

type BrandMarkProps = {
  variant?: 'icon' | 'lockup';
  className?: string;
};

export const BrandMark: React.FC<BrandMarkProps> = ({ variant = 'icon', className }) => {
  const label = `${APP_BRAND.chineseName} ${APP_BRAND.englishName}`;

  if (variant === 'lockup') {
    return (
      <span className={cn('inline-flex', className)} role="img" aria-label={label} data-testid="brand-lockup">
        <img
          src="/brand/logo-light.svg"
          alt=""
          aria-hidden="true"
          draggable={false}
          className="block h-full w-full object-contain dark:hidden"
        />
        <img
          src="/brand/logo-dark.svg"
          alt=""
          aria-hidden="true"
          draggable={false}
          className="hidden h-full w-full object-contain dark:block"
        />
      </span>
    );
  }

  return (
    <img
      src="/brand/icon.svg"
      alt={`${APP_BRAND.chineseName} 图标`}
      draggable={false}
      className={cn('object-contain', className)}
      data-testid="brand-icon"
    />
  );
};
