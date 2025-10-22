/**
 * Tests for Modal component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Modal } from './Modal';

describe('Modal', () => {
  it('renders when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>Modal content</div>
      </Modal>
    );
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={vi.fn()}>
        <div>Modal content</div>
      </Modal>
    );
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} title="Modal Title">
        <div>Content</div>
      </Modal>
    );
    expect(screen.getByText('Modal Title')).toBeInTheDocument();
  });

  it('does not render header when no title and showCloseButton is false', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()} showCloseButton={false}>
        <div>Content</div>
      </Modal>
    );
    const header = container.querySelector('.border-b');
    expect(header).not.toBeInTheDocument();
  });

  it('renders close button by default', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>Content</div>
      </Modal>
    );
    const closeButton = screen.getByRole('button');
    expect(closeButton).toBeInTheDocument();
  });

  it('hides close button when showCloseButton is false', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()} showCloseButton={false}>
        <div>Content</div>
      </Modal>
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('calls onClose when close button clicked', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    const closeButton = screen.getByRole('button');
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when backdrop clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <Modal isOpen={true} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    const backdrop = container.querySelector('.fixed.inset-0');
    fireEvent.click(backdrop!);

    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not close when modal content clicked', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    fireEvent.click(screen.getByText('Content'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('calls onClose when Escape key pressed', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not call onClose for other keys', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose}>
        <div>Content</div>
      </Modal>
    );

    fireEvent.keyDown(document, { key: 'Enter' });
    expect(onClose).not.toHaveBeenCalled();
  });

  it('applies small size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()} size="sm">
        <div>Content</div>
      </Modal>
    );
    const modalContent = container.querySelector('.bg-slate-800');
    expect(modalContent).toHaveClass('max-w-sm');
  });

  it('applies medium size by default', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>Content</div>
      </Modal>
    );
    const modalContent = container.querySelector('.bg-slate-800');
    expect(modalContent).toHaveClass('max-w-md');
  });

  it('applies large size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()} size="lg">
        <div>Content</div>
      </Modal>
    );
    const modalContent = container.querySelector('.bg-slate-800');
    expect(modalContent).toHaveClass('max-w-2xl');
  });

  it('applies extra large size', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()} size="xl">
        <div>Content</div>
      </Modal>
    );
    const modalContent = container.querySelector('.bg-slate-800');
    expect(modalContent).toHaveClass('max-w-4xl');
  });

  it('renders children correctly', () => {
    render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>
          <h3>Heading</h3>
          <p>Paragraph</p>
        </div>
      </Modal>
    );
    expect(screen.getByText('Heading')).toBeInTheDocument();
    expect(screen.getByText('Paragraph')).toBeInTheDocument();
  });

  it('has backdrop blur', () => {
    const { container } = render(
      <Modal isOpen={true} onClose={vi.fn()}>
        <div>Content</div>
      </Modal>
    );
    const backdrop = container.querySelector('.fixed.inset-0');
    expect(backdrop).toHaveClass('backdrop-blur-sm');
  });
});
