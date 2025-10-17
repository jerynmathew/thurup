/**
 * Input component tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from './Input';

describe('Input', () => {
  it('renders input with label', () => {
    render(<Input label="Username" value="" onChange={() => {}} />);
    expect(screen.getByText('Username')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders without label', () => {
    render(<Input value="" onChange={() => {}} />);
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });

  it('calls onChange when value changes', () => {
    const onChange = vi.fn();
    render(<Input value="" onChange={onChange} />);

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'test' } });

    expect(onChange).toHaveBeenCalled();
  });

  it('applies fullWidth class to wrapper', () => {
    const { container } = render(<Input value="" onChange={() => {}} fullWidth />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('w-full');
  });

  it('applies custom className', () => {
    const { container } = render(<Input value="" onChange={() => {}} className="custom-class" />);
    const input = container.querySelector('input');
    expect(input).toHaveClass('custom-class');
  });

  it('displays placeholder text', () => {
    render(<Input value="" onChange={() => {}} placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('can be disabled', () => {
    render(<Input value="" onChange={() => {}} disabled />);
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('can be required', () => {
    render(<Input value="" onChange={() => {}} required />);
    const input = screen.getByRole('textbox') as HTMLInputElement;
    expect(input.required).toBe(true);
  });

  it('supports different input types', () => {
    const { rerender, container } = render(<Input type="password" value="" onChange={() => {}} />);
    let input = container.querySelector('input') as HTMLInputElement;
    expect(input.type).toBe('password');

    rerender(<Input type="email" value="" onChange={() => {}} />);
    input = container.querySelector('input') as HTMLInputElement;
    expect(input.type).toBe('email');
  });

  it('displays error message', () => {
    render(<Input value="" onChange={() => {}} error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('applies error styling when error is present', () => {
    const { container } = render(<Input value="" onChange={() => {}} error="Error message" />);
    const input = container.querySelector('input');
    expect(input).toHaveClass('border-red-500');
  });

  it('can be required', () => {
    const { container } = render(<Input label="Name" value="" onChange={() => {}} required />);
    const input = container.querySelector('input') as HTMLInputElement;
    expect(input.required).toBe(true);
  });
});
