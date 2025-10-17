/**
 * TrumpPanel component tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrumpPanel } from './TrumpPanel';

describe('TrumpPanel', () => {
  const defaultProps = {
    onSelectTrump: vi.fn(),
    isMyTurn: true,
  };

  it('renders trump selection panel correctly', () => {
    render(<TrumpPanel {...defaultProps} />);
    expect(screen.getByText('Choose Trump')).toBeInTheDocument();
    expect(screen.getByText(/You won the bidding!/)).toBeInTheDocument();
  });

  it('renders all four suits', () => {
    render(<TrumpPanel {...defaultProps} />);

    expect(screen.getByText('♠')).toBeInTheDocument();
    expect(screen.getByText('♥')).toBeInTheDocument();
    expect(screen.getByText('♦')).toBeInTheDocument();
    expect(screen.getByText('♣')).toBeInTheDocument();
  });

  it('renders suit names', () => {
    render(<TrumpPanel {...defaultProps} />);

    expect(screen.getByText('Spades')).toBeInTheDocument();
    expect(screen.getByText('Hearts')).toBeInTheDocument();
    expect(screen.getByText('Diamonds')).toBeInTheDocument();
    expect(screen.getByText('Clubs')).toBeInTheDocument();
  });

  it('calls onSelectTrump when suit button is clicked', () => {
    const onSelectTrump = vi.fn();
    render(<TrumpPanel {...defaultProps} onSelectTrump={onSelectTrump} />);

    const spadesButton = screen.getByText('Spades').closest('button');
    fireEvent.click(spadesButton!);

    expect(onSelectTrump).toHaveBeenCalledWith('♠');
  });

  it('hides buttons when not my turn', () => {
    render(<TrumpPanel {...defaultProps} isMyTurn={false} />);

    // Should show waiting message
    expect(screen.getByText(/Waiting for bid winner/)).toBeInTheDocument();

    // Should not show suit buttons
    expect(screen.queryByText('Spades')).not.toBeInTheDocument();
  });

  it('enables all buttons when my turn', () => {
    render(<TrumpPanel {...defaultProps} isMyTurn={true} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).not.toBeDisabled();
    });
  });

  it('calls onSelectTrump with correct suit for each button', () => {
    const onSelectTrump = vi.fn();
    render(<TrumpPanel {...defaultProps} onSelectTrump={onSelectTrump} />);

    // Click spades
    fireEvent.click(screen.getByText('Spades').closest('button')!);
    expect(onSelectTrump).toHaveBeenCalledWith('♠');

    onSelectTrump.mockClear();

    // Click hearts
    fireEvent.click(screen.getByText('Hearts').closest('button')!);
    expect(onSelectTrump).toHaveBeenCalledWith('♥');
  });

  it('displays waiting message when not my turn', () => {
    render(<TrumpPanel {...defaultProps} isMyTurn={false} />);
    expect(screen.getByText(/Waiting for bid winner/)).toBeInTheDocument();
  });
});
