/**
 * Tests for Select component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Select } from './Select';

describe('Select', () => {
  it('renders select element', () => {
    render(
      <Select>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
      </Select>
    );
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('renders label when provided', () => {
    render(
      <Select label="Choose option">
        <option>Option</option>
      </Select>
    );
    expect(screen.getByText('Choose option')).toBeInTheDocument();
  });

  it('does not render label when not provided', () => {
    render(
      <Select>
        <option>Option</option>
      </Select>
    );
    expect(screen.queryByText('Choose option')).not.toBeInTheDocument();
  });

  it('renders error message', () => {
    render(
      <Select error="This field is required">
        <option>Option</option>
      </Select>
    );
    expect(screen.getByText('This field is required')).toBeInTheDocument();
  });

  it('applies error styles when error is present', () => {
    render(
      <Select error="Error message">
        <option>Option</option>
      </Select>
    );
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('border-red-500');
  });

  it('handles onChange event', () => {
    const handleChange = vi.fn();
    render(
      <Select onChange={handleChange}>
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
      </Select>
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '2' } });

    expect(handleChange).toHaveBeenCalledOnce();
  });

  it('supports disabled state', () => {
    render(
      <Select disabled>
        <option>Option</option>
      </Select>
    );
    expect(screen.getByRole('combobox')).toBeDisabled();
  });

  it('applies disabled styles', () => {
    render(
      <Select disabled>
        <option>Option</option>
      </Select>
    );
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('disabled:opacity-50');
    expect(select).toHaveClass('disabled:cursor-not-allowed');
  });

  it('applies fullWidth class', () => {
    const { container } = render(
      <Select fullWidth>
        <option>Option</option>
      </Select>
    );
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('w-full');
  });

  it('does not apply fullWidth by default', () => {
    const { container } = render(
      <Select>
        <option>Option</option>
      </Select>
    );
    const wrapper = container.firstChild;
    expect(wrapper).not.toHaveClass('w-full');
  });

  it('applies custom className', () => {
    render(
      <Select className="custom-class">
        <option>Option</option>
      </Select>
    );
    const select = screen.getByRole('combobox');
    expect(select).toHaveClass('custom-class');
  });

  it('renders multiple options', () => {
    render(
      <Select>
        <option value="1">First</option>
        <option value="2">Second</option>
        <option value="3">Third</option>
      </Select>
    );
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
    expect(screen.getByText('Third')).toBeInTheDocument();
  });

  it('supports default value', () => {
    render(
      <Select defaultValue="2">
        <option value="1">First</option>
        <option value="2">Second</option>
      </Select>
    );
    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('2');
  });
});
