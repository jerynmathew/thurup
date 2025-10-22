/**
 * Tests for Badge component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from './Badge';

describe('Badge', () => {
  it('renders children', () => {
    render(<Badge>Test Badge</Badge>);
    expect(screen.getByText('Test Badge')).toBeInTheDocument();
  });

  it('applies default variant by default', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toHaveClass('bg-slate-700');
    expect(badge).toHaveClass('text-slate-200');
  });

  it('applies primary variant', () => {
    render(<Badge variant="primary">Primary</Badge>);
    const badge = screen.getByText('Primary');
    expect(badge).toHaveClass('bg-primary-500/20');
    expect(badge).toHaveClass('text-primary-300');
  });

  it('applies success variant', () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText('Success');
    expect(badge).toHaveClass('bg-green-500/20');
    expect(badge).toHaveClass('text-green-300');
  });

  it('applies warning variant', () => {
    render(<Badge variant="warning">Warning</Badge>);
    const badge = screen.getByText('Warning');
    expect(badge).toHaveClass('bg-yellow-500/20');
    expect(badge).toHaveClass('text-yellow-300');
  });

  it('applies danger variant', () => {
    render(<Badge variant="danger">Danger</Badge>);
    const badge = screen.getByText('Danger');
    expect(badge).toHaveClass('bg-red-500/20');
    expect(badge).toHaveClass('text-red-300');
  });

  it('applies info variant', () => {
    render(<Badge variant="info">Info</Badge>);
    const badge = screen.getByText('Info');
    expect(badge).toHaveClass('bg-blue-500/20');
    expect(badge).toHaveClass('text-blue-300');
  });

  it('applies small size', () => {
    render(<Badge size="sm">Small</Badge>);
    const badge = screen.getByText('Small');
    expect(badge).toHaveClass('px-2');
    expect(badge).toHaveClass('py-0.5');
    expect(badge).toHaveClass('text-xs');
  });

  it('applies medium size by default', () => {
    render(<Badge>Medium</Badge>);
    const badge = screen.getByText('Medium');
    expect(badge).toHaveClass('px-3');
    expect(badge).toHaveClass('py-1');
    expect(badge).toHaveClass('text-sm');
  });

  it('applies custom className', () => {
    render(<Badge className="custom-class">Custom</Badge>);
    const badge = screen.getByText('Custom');
    expect(badge).toHaveClass('custom-class');
  });

  it('renders with complex children', () => {
    render(
      <Badge>
        <span>Icon</span> Label
      </Badge>
    );
    expect(screen.getByText('Icon')).toBeInTheDocument();
    expect(screen.getByText('Label')).toBeInTheDocument();
  });
});
