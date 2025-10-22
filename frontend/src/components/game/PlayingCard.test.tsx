/**
 * Tests for PlayingCard component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlayingCard } from './PlayingCard';
import { mockCard, mockCards } from '../../test/mockData';

describe('PlayingCard', () => {
  it('renders card image', () => {
    render(<PlayingCard card={mockCard} />);
    const img = screen.getByRole('img');
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute('alt', 'A♠');
  });

  it('renders correct image for hearts', () => {
    const heartCard = { ...mockCard, suit: '♥' as const };
    render(<PlayingCard card={heartCard} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://deckofcardsapi.com/static/img/AH.png');
  });

  it('renders correct image for diamonds', () => {
    const diamondCard = { ...mockCard, suit: '♦' as const };
    render(<PlayingCard card={diamondCard} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://deckofcardsapi.com/static/img/AD.png');
  });

  it('renders correct image for spades', () => {
    render(<PlayingCard card={mockCard} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://deckofcardsapi.com/static/img/AS.png');
  });

  it('renders correct image for clubs', () => {
    const clubCard = { ...mockCard, suit: '♣' as const };
    render(<PlayingCard card={clubCard} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://deckofcardsapi.com/static/img/AC.png');
  });

  it('shows playable indicator when isPlayable is true', () => {
    const { container } = render(<PlayingCard card={mockCard} isPlayable={true} />);
    expect(container.querySelector('.bg-primary-500.rounded-full')).toBeInTheDocument();
  });

  it('does not show playable indicator when isPlayable is false', () => {
    const { container } = render(<PlayingCard card={mockCard} isPlayable={false} />);
    expect(container.querySelector('.bg-primary-500.rounded-full')).not.toBeInTheDocument();
  });

  it('applies playable styles when isPlayable is true', () => {
    render(<PlayingCard card={mockCard} isPlayable={true} />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('border-primary-500');
  });

  it('calls onClick when clicked and not disabled', () => {
    const onClick = vi.fn();
    render(<PlayingCard card={mockCard} onClick={onClick} isPlayable={true} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('does not call onClick when disabled', () => {
    const onClick = vi.fn();
    render(<PlayingCard card={mockCard} onClick={onClick} disabled={true} />);
    fireEvent.click(screen.getByRole('button'));
    expect(onClick).not.toHaveBeenCalled();
  });

  it('is disabled when disabled prop is true', () => {
    render(<PlayingCard card={mockCard} disabled={true} />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies small size correctly', () => {
    render(<PlayingCard card={mockCard} size="sm" />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-16');
    expect(button).toHaveClass('h-24');
  });

  it('applies medium size correctly', () => {
    render(<PlayingCard card={mockCard} size="md" />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-20');
    expect(button).toHaveClass('h-28');
  });

  it('applies large size correctly', () => {
    render(<PlayingCard card={mockCard} size="lg" />);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('w-24');
    expect(button).toHaveClass('h-32');
  });

  it('applies opacity when disabled', () => {
    render(<PlayingCard card={mockCard} disabled={true} />);
    expect(screen.getByRole('button')).toHaveClass('opacity-50');
  });
});
