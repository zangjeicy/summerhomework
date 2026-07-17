import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { Card } from '../Card';

describe('Card', () => {
  it.each(['default', 'bordered'] as const)(
    'routes the %s variant through the shared card surface contract',
    (variant) => {
      const { container } = render(<Card variant={variant}>Card content</Card>);
      const card = container.firstElementChild;

      expect(card).toHaveClass('surface-card', 'terminal-card');
      expect(card).not.toHaveClass('rounded-2xl');
    },
  );

  it('uses the semantic gradient surface class for the gradient variant', () => {
    const { container } = render(<Card variant="gradient">Gradient content</Card>);
    const card = container.firstElementChild;

    expect(card).toHaveClass('surface-card-gradient', 'gradient-border-card');
    expect(card).not.toHaveClass('rounded-2xl');
  });
});
