/**
 * Tests for PlayerHand component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PlayerHand } from './PlayerHand';
import { mockCard, mockCards } from '../../test/mockData';

describe('PlayerHand', () => {
  it('shows empty state when no cards', () => {
    render(<PlayerHand cards={[]} />);
    expect(screen.getByText('No cards in hand')).toBeInTheDocument();
  });

  it('renders cards', () => {
    render(<PlayerHand cards={mockCards.slice(0, 3)} />);
    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(3);
  });

  it('shows card count', () => {
    render(<PlayerHand cards={mockCards.slice(0, 5)} />);
    expect(screen.getByText(/5 cards/)).toBeInTheDocument();
  });

  it('shows singular card count for one card', () => {
    render(<PlayerHand cards={[mockCard]} />);
    expect(screen.getByText(/1 card$/)).toBeInTheDocument();
  });

  it('shows playable count when some cards are playable', () => {
    const cards = mockCards.slice(0, 5);
    const playableCards = [cards[0].id, cards[2].id];

    render(<PlayerHand cards={cards} playableCards={playableCards} />);
    expect(screen.getByText(/\(2 playable\)/)).toBeInTheDocument();
  });

  it('does not show playable count when all cards are playable', () => {
    const cards = mockCards.slice(0, 3);
    const playableCards = cards.map(c => c.id);

    render(<PlayerHand cards={cards} playableCards={playableCards} />);
    expect(screen.queryByText(/playable/)).not.toBeInTheDocument();
  });

  it('calls onCardClick when playable card is clicked', () => {
    const onCardClick = vi.fn();
    const cards = [mockCard];
    const playableCards = [mockCard.id];

    render(
      <PlayerHand
        cards={cards}
        playableCards={playableCards}
        onCardClick={onCardClick}
      />
    );

    const cardButton = screen.getByRole('button');
    fireEvent.click(cardButton);

    expect(onCardClick).toHaveBeenCalledWith(mockCard);
  });

  it('does not call onCardClick when non-playable card is clicked', () => {
    const onCardClick = vi.fn();
    const cards = [mockCard];
    const playableCards: string[] = [];

    render(
      <PlayerHand
        cards={cards}
        playableCards={playableCards}
        onCardClick={onCardClick}
      />
    );

    const cardButton = screen.getByRole('button');
    fireEvent.click(cardButton);

    expect(onCardClick).not.toHaveBeenCalled();
  });

  it('does not call onCardClick when disabled', () => {
    const onCardClick = vi.fn();
    const cards = [mockCard];
    const playableCards = [mockCard.id];

    render(
      <PlayerHand
        cards={cards}
        playableCards={playableCards}
        onCardClick={onCardClick}
        disabled={true}
      />
    );

    const cardButton = screen.getByRole('button');
    fireEvent.click(cardButton);

    expect(onCardClick).not.toHaveBeenCalled();
  });

  it('shows reveal trump button when canRevealTrump is true', () => {
    const onRevealTrump = vi.fn();

    render(
      <PlayerHand
        cards={[mockCard]}
        canRevealTrump={true}
        onRevealTrump={onRevealTrump}
      />
    );

    expect(screen.getByText('Reveal Trump')).toBeInTheDocument();
  });

  it('does not show reveal trump button when canRevealTrump is false', () => {
    const onRevealTrump = vi.fn();

    render(
      <PlayerHand
        cards={[mockCard]}
        canRevealTrump={false}
        onRevealTrump={onRevealTrump}
      />
    );

    expect(screen.queryByText('Reveal Trump')).not.toBeInTheDocument();
  });

  it('calls onRevealTrump when reveal button clicked', () => {
    const onRevealTrump = vi.fn();

    render(
      <PlayerHand
        cards={[mockCard]}
        canRevealTrump={true}
        onRevealTrump={onRevealTrump}
      />
    );

    const revealButton = screen.getByText('Reveal Trump');
    fireEvent.click(revealButton);

    expect(onRevealTrump).toHaveBeenCalledOnce();
  });

  it('renders cards with correct z-index', () => {
    const cards = mockCards.slice(0, 3);
    const { container } = render(<PlayerHand cards={cards} />);

    const cardWrappers = container.querySelectorAll('.transition-transform');
    expect(cardWrappers[0]).toHaveStyle({ zIndex: '0' });
    expect(cardWrappers[1]).toHaveStyle({ zIndex: '1' });
    expect(cardWrappers[2]).toHaveStyle({ zIndex: '2' });
  });

  it('applies playable styles to playable cards', () => {
    const cards = mockCards.slice(0, 2);
    const playableCards = [cards[0].id];

    render(<PlayerHand cards={cards} playableCards={playableCards} />);

    const cardButtons = screen.getAllByRole('button');
    expect(cardButtons[0]).toHaveClass('border-primary-500');
    expect(cardButtons[1]).not.toHaveClass('border-primary-500');
  });
});
