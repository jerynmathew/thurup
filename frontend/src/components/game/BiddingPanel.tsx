/**
 * BiddingPanel component - handles the bidding phase.
 */

import { useState } from 'react';
import { NeonButton } from '../ui';

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
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-neon-amber">Place Your Bid</h3>

      {!isMyTurn && (
        <div className="p-3 bg-white/5 rounded border border-white/10 text-center">
          <p className="text-slate-400 text-sm animate-pulse">Waiting for your turn...</p>
        </div>
      )}

      {isMyTurn && (
        <>
          <div className="bg-white/5 p-3 rounded border border-white/10">
            <p className="text-slate-300 text-sm mb-1">
              {currentHighBid !== null ? (
                <>Current High: <span className="font-bold text-neon-cyan">{currentHighBid}</span></>
              ) : (
                <>Minimum Bid: <span className="font-bold text-neon-cyan">{minBid}</span></>
              )}
            </p>
            <p className="text-xs text-slate-500">
              Min valid bid: {minValidBid}
            </p>
          </div>

          {/* Quick Bid Buttons */}
          <div className="grid grid-cols-2 gap-2">
            {quickBids.map((bid) => (
              <NeonButton
                key={bid}
                variant="cyan"
                className="py-1 text-sm"
                onClick={() => onBid(bid)}
                disabled={!canBid}
              >
                Bid {bid}
              </NeonButton>
            ))}
          </div>

          {/* Custom Bid */}
          <div className="flex gap-2">
            <input
              type="number"
              min={minValidBid}
              max={28}
              value={customBid}
              onChange={(e) => setCustomBid(e.target.value)}
              placeholder={`${minValidBid}-28`}
              disabled={!canBid}
              className="flex-1 px-3 py-1.5 bg-black/30 border border-white/20 rounded text-white placeholder-slate-500 focus:outline-none focus:border-neon-cyan text-sm"
            />
            <NeonButton
              variant="cyan"
              className="py-1 px-4 text-sm"
              onClick={handleCustomBid}
              disabled={!canBid || !customBid}
            >
              Bid
            </NeonButton>
          </div>

          {/* Pass Button */}
          <NeonButton
            variant="danger"
            className="w-full py-1.5 text-sm bg-red-900/50 hover:bg-red-800/50 border border-red-500/30"
            onClick={onPass}
            disabled={!canBid}
          >
            Pass
          </NeonButton>
        </>
      )}
    </div>
  );
}
