/**
 * BiddingPanel component - handles the bidding phase.
 */

import { useState } from 'react';
import { Button, Card } from '../ui';

interface BiddingPanelProps {
  minBid: number;
  currentHighBid: number | null;
  onBid: (value: number) => void;
  onPass: () => void;
  disabled?: boolean;
  isMyTurn: boolean;
}

export function BiddingPanel({
  minBid,
  currentHighBid,
  onBid,
  onPass,
  disabled = false,
  isMyTurn,
}: BiddingPanelProps) {
  const [customBid, setCustomBid] = useState<string>('');

  // Calculate minimum valid bid
  const minValidBid = currentHighBid !== null ? currentHighBid + 1 : minBid;

  // Quick bid options (increments of 4)
  const quickBids = [];
  for (let i = minValidBid; i <= 28 && quickBids.length < 4; i += 4) {
    quickBids.push(i);
  }

  const handleCustomBid = () => {
    const value = parseInt(customBid);
    if (!isNaN(value) && value >= minValidBid && value <= 28) {
      onBid(value);
      setCustomBid('');
    }
  };

  const canBid = isMyTurn && !disabled;

  return (
    <Card padding="md">
      <h3 className="text-lg font-semibold mb-4">Bidding</h3>

      {!isMyTurn && (
        <p className="text-slate-400 text-sm mb-4">Waiting for your turn...</p>
      )}

      {isMyTurn && (
        <>
          <div className="mb-4">
            <p className="text-slate-300 text-sm mb-2">
              {currentHighBid !== null ? (
                <>Current bid: <span className="font-bold text-primary-400">{currentHighBid}</span></>
              ) : (
                <>Minimum bid: <span className="font-bold text-primary-400">{minBid}</span></>
              )}
            </p>
            <p className="text-slate-400 text-xs">
              You must bid at least {minValidBid}
            </p>
          </div>

          {/* Quick Bid Buttons */}
          <div className="grid grid-cols-2 gap-2 mb-4">
            {quickBids.map((bid) => (
              <Button
                key={bid}
                variant="primary"
                onClick={() => onBid(bid)}
                disabled={!canBid}
              >
                Bid {bid}
              </Button>
            ))}
          </div>

          {/* Custom Bid */}
          <div className="mb-4">
            <div className="flex gap-2">
              <input
                type="number"
                min={minValidBid}
                max={28}
                value={customBid}
                onChange={(e) => setCustomBid(e.target.value)}
                placeholder={`${minValidBid}-28`}
                disabled={!canBid}
                className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
              <Button
                variant="primary"
                onClick={handleCustomBid}
                disabled={!canBid || !customBid}
              >
                Bid
              </Button>
            </div>
          </div>

          {/* Pass Button */}
          <Button
            variant="danger"
            fullWidth
            onClick={onPass}
            disabled={!canBid}
          >
            Pass
          </Button>
        </>
      )}
    </Card>
  );
}
