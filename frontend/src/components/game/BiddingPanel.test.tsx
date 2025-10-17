/**
 * BiddingPanel component tests.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BiddingPanel } from './BiddingPanel';

describe('BiddingPanel', () => {
  const defaultProps = {
    minBid: 16,
    currentHighBid: null,
    onBid: vi.fn(),
    onPass: vi.fn(),
    isMyTurn: true,
  };

  it('renders bidding panel correctly', () => {
    render(<BiddingPanel {...defaultProps} />);
    expect(screen.getByText('Bidding')).toBeInTheDocument();
    expect(screen.getByText('Pass')).toBeInTheDocument();
  });

  it('displays minimum bid correctly', () => {
    render(<BiddingPanel {...defaultProps} />);
    expect(screen.getByText('Minimum bid:')).toBeInTheDocument();
    expect(screen.getByText('16')).toBeInTheDocument();
  });

  it('displays current high bid when present', () => {
    render(<BiddingPanel {...defaultProps} currentHighBid={20} />);
    expect(screen.getByText('Current bid:')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('calls onBid when quick bid button is clicked', () => {
    const onBid = vi.fn();
    render(<BiddingPanel {...defaultProps} onBid={onBid} />);

    const bidButton = screen.getByText('Bid 16');
    fireEvent.click(bidButton);

    expect(onBid).toHaveBeenCalledWith(16);
  });

  it('calls onPass when pass button is clicked', () => {
    const onPass = vi.fn();
    render(<BiddingPanel {...defaultProps} onPass={onPass} />);

    const passButton = screen.getByText('Pass');
    fireEvent.click(passButton);

    expect(onPass).toHaveBeenCalled();
  });

  it('hides controls when not my turn', () => {
    render(<BiddingPanel {...defaultProps} isMyTurn={false} />);

    // Should show waiting message
    expect(screen.getByText(/Waiting for your turn/)).toBeInTheDocument();

    // Should not show bidding controls
    expect(screen.queryByText('Pass')).not.toBeInTheDocument();
  });

  it('disables all buttons when disabled prop is true', () => {
    render(<BiddingPanel {...defaultProps} disabled={true} isMyTurn={true} />);

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('shows custom bid input', () => {
    render(<BiddingPanel {...defaultProps} />);

    const input = screen.getByPlaceholderText('16-28');
    expect(input).toBeInTheDocument();
  });

  it('calls onBid with custom value when custom bid is submitted', () => {
    const onBid = vi.fn();
    render(<BiddingPanel {...defaultProps} onBid={onBid} />);

    const input = screen.getByPlaceholderText('16-28') as HTMLInputElement;
    const buttons = screen.getAllByText('Bid');
    const submitButton = buttons[buttons.length - 1]; // Last "Bid" button is the custom one

    fireEvent.change(input, { target: { value: '25' } });
    fireEvent.click(submitButton);

    expect(onBid).toHaveBeenCalledWith(25);
  });

  it('does not call onBid with invalid custom value', () => {
    const onBid = vi.fn();
    render(<BiddingPanel {...defaultProps} />);

    const input = screen.getByPlaceholderText('16-28') as HTMLInputElement;
    const buttons = screen.getAllByText('Bid');
    const submitButton = buttons[buttons.length - 1];

    fireEvent.change(input, { target: { value: '10' } }); // Below min
    fireEvent.click(submitButton);

    expect(onBid).not.toHaveBeenCalled();
  });

  it('filters quick bid buttons based on current high bid', () => {
    render(<BiddingPanel {...defaultProps} currentHighBid={18} minBid={16} />);

    // minValidBid = 19 (current high bid + 1)
    // Quick bids: 19, 23, 27 (increments of 4 from 19)
    expect(screen.queryByText('Bid 16')).not.toBeInTheDocument();
    expect(screen.getByText('Bid 19')).toBeInTheDocument();
    expect(screen.getByText('Bid 23')).toBeInTheDocument();
  });
});
