"""
Bot runner logic for automated AI players.

Handles bot decision-making and action execution in a sequential manner.
"""

import asyncio
import traceback

from app.api.v1.broadcast import broadcast_state
from app.api.v1.router import SESSIONS, bot_tasks
from app.constants import BotConfig
from app.game import ai as ai_module
from app.game.session import SessionState
from app.logging_config import get_logger
from app.models import BidCmd, ChooseTrumpCmd, PlayCardCmd

logger = get_logger(__name__)


def schedule_bot_runner(game_id: str):
    """
    Safely schedule a bot runner task, ensuring only one runs at a time per game.

    If a bot runner is already active for this game, this is a no-op.
    When the task completes, it automatically cleans up its reference.
    """
    # Check if there's already a running task for this game
    existing_task = bot_tasks.get(game_id)
    if existing_task and not existing_task.done():
        # Bot runner already active, don't schedule another
        return

    # Schedule new bot runner task
    task = asyncio.create_task(run_bots_for_game(game_id))
    bot_tasks[game_id] = task

    # Cleanup task reference when done
    def cleanup(t):
        if bot_tasks.get(game_id) == t:
            bot_tasks.pop(game_id, None)

    task.add_done_callback(cleanup)


async def run_bots_for_game(
    game_id: str,
    delay: float = BotConfig.ACTION_DELAY_SECONDS,
    max_cycles: int = BotConfig.MAX_CYCLES_PER_RUN,
):
    """
    Sequential bot-runner that handles bot actions for the current game phase.

    Phases handled:
    - BIDDING: Only consider sess.turn (the next bidder). If that seat is a bot, ask it to act.
    - CHOOSE_TRUMP: Only the bid_winner acts.
    - PLAY: Only the seat equal to sess.turn acts.

    Loops until there is no bot action to take or max_cycles reached.
    """
    sess = SESSIONS.get(game_id)
    if not sess:
        return

    cycles = 0
    try:
        while cycles < max_cycles:
            cycles += 1
            acted = False

            # BIDDING phase: only current turn may bid
            if sess.state == SessionState.BIDDING:
                acted = await _handle_bidding_bot(game_id, sess, delay)
                if not acted:
                    break
                continue

            # CHOOSE_TRUMP phase: only bid_winner chooses
            if sess.state == SessionState.CHOOSE_TRUMP:
                acted = await _handle_choose_trump_bot(game_id, sess, delay)
                if not acted:
                    break
                continue

            # PLAY phase: only sess.turn may act
            if sess.state == SessionState.PLAY:
                acted = await _handle_play_bot(game_id, sess, delay)
                if not acted:
                    break
                continue

            # if we reached here and no action was made, exit loop
            if not acted:
                break

    except Exception as e:
        logger.error(
            "bot_runner_exception",
            game_id=game_id,
            error=str(e),
            traceback=traceback.format_exc(),
        )
    finally:
        try:
            await broadcast_state(game_id)
        except Exception as e:
            logger.error(
                "bot_runner_broadcast_failed",
                game_id=game_id,
                error=str(e),
                traceback=traceback.format_exc(),
            )
        logger.debug("bot_runner_finished", game_id=game_id, cycles=cycles)


async def _handle_bidding_bot(game_id: str, sess, delay: float) -> bool:
    """Handle bot action in BIDDING phase. Returns True if action was taken."""
    seat = sess.turn
    p = sess.players.get(seat)

    # If seat is bot and still waiting to act (None), ask it
    if not (p and getattr(p, "is_bot", False) and sess.bidding_manager.bids.get(seat) is None):
        return False

    try:
        suggested = sess.force_bot_play_choice(seat, ai_module)
    except Exception as e:
        logger.error(
            "bot_decision_failed",
            game_id=game_id,
            seat=seat,
            phase="bidding",
            error=str(e),
        )
        return False

    if not (suggested and suggested["type"] == "place_bid"):
        return False

    await asyncio.sleep(delay)
    val = suggested["payload"]["value"]
    ok, msg = await sess.place_bid(seat, BidCmd(value=val))
    logger.info(
        "bot_action",
        game_id=game_id,
        seat=seat,
        action="place_bid",
        value=val,
        success=ok,
        message=msg,
    )
    await broadcast_state(game_id)
    return True


async def _handle_choose_trump_bot(game_id: str, sess, delay: float) -> bool:
    """Handle bot action in CHOOSE_TRUMP phase. Returns True if action was taken."""
    seat = sess.bidding_manager.bid_winner
    if seat is None:
        # no numeric bids; nothing to do
        return False

    p = sess.players.get(seat)
    if not (p and getattr(p, "is_bot", False)):
        return False

    try:
        suggested = sess.force_bot_play_choice(seat, ai_module)
    except Exception as e:
        logger.error(
            "bot_decision_failed",
            game_id=game_id,
            seat=seat,
            phase="choose_trump",
            error=str(e),
        )
        return False

    if not (suggested and suggested["type"] == "choose_trump"):
        return False

    await asyncio.sleep(delay)
    suit = suggested["payload"]["suit"]
    ok, msg = await sess.choose_trump(seat, ChooseTrumpCmd(suit=suit))
    logger.info(
        "bot_action",
        game_id=game_id,
        seat=seat,
        action="choose_trump",
        suit=suit,
        success=ok,
        message=msg,
    )
    await broadcast_state(game_id)
    return True


async def _handle_play_bot(game_id: str, sess, delay: float) -> bool:
    """Handle bot action in PLAY phase. Returns True if action was taken."""
    seat = sess.turn
    p = sess.players.get(seat)

    if not (p and getattr(p, "is_bot", False)):
        return False

    try:
        suggested = sess.force_bot_play_choice(seat, ai_module)
    except Exception as e:
        logger.error(
            "bot_decision_failed",
            game_id=game_id,
            seat=seat,
            phase="play",
            error=str(e),
        )
        return False

    if not (suggested and suggested["type"] == "play_card"):
        return False

    await asyncio.sleep(delay)
    cid = suggested["payload"]["card_id"]
    ok, msg = await sess.play_card(seat, PlayCardCmd(card_id=cid))
    logger.info(
        "bot_action",
        game_id=game_id,
        seat=seat,
        action="play_card",
        card_id=cid,
        success=ok,
        message=msg,
    )
    await broadcast_state(game_id)
    return True
