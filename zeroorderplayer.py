from toepen import ToepPlayer, ToepController, ToepPlay  # noqa
import random #noqa


class ZeroOrderPlayer(ToepPlayer):
    def start_game(self, identifier: int, cards: tuple[str], rank_strength):
        self.identifier = identifier
        self.rank_strength = rank_strength
        self.hand_strength = sum(rank_strength[rank] for rank, _ in cards)
        self.void_suits = {i: set() for i in range(4)}
    
    
    def observe_play(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        player_id: int,
        previous_play: ToepPlay,
        lead_suit: str,
        trick_before_play: list[ToepPlay],
    ) -> None:
        # Build a belief set on the hand of opponents (actually the deck for ToM0)
        if lead_suit is not None and previous_play.suit != lead_suit:
            self.void_suits[player_id].add(lead_suit)

    def call_toep(
        self, cards: tuple[str, str], ante: int, lead_suit: str | None
    ) -> str | None:
        # Must be leading (otherwise no control)
        if lead_suit is not None:
            return None
        suits = {s for _, s in cards}
        if len(suits) != 1:
            return None
        suit = next(iter(suits))
        for opp_id, voids in self.void_suits.items():
            if suit not in voids:
                return None  # Not certain
        return "TOEP"

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return "MEEGAAN"

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        # Only call witte was when having 4 cards.
        face_cards = {"J", "Q", "K", "A"}
        if all(rank in face_cards for rank, suit in cards):
            return "WITTE_WAS"
        return "NONE"

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:
        # Always believe opponent
        return "BELIEVE"


class PessimisticZeroOrderPlayer(ZeroOrderPlayer):
    """Always plays the lowest card in hand, in order to end with the strongest card."""
    def take_turn(
        self, cards: tuple[str, str], player_count: int, current_suit: str, trick
    ) -> str:
        if current_suit is None:  # ToM1 plays initial card
            return min(
                cards, key=lambda c: self.rank_strength[c[0]]
            )  # throw away lowest ranked card to finish with highest
        same_suit = [c for c in cards if c[1] == current_suit]

        if same_suit:
            return min(same_suit, key=lambda c: self.rank_strength[c[0]])
        return min(cards, key=lambda c: self.rank_strength[c[0]])

class OptimisticZeroOrderPlayer(ZeroOrderPlayer):
    """Always play highest card in hand (following suit)."""
    def take_turn(
        self, cards: tuple[str, str], player_count: int, current_suit: str, trick
    ) -> str:
        if current_suit is None:  # ToM1 plays initial card
            return max(
                cards, key=lambda c: self.rank_strength[c[0]]
            )  # throw away lowest ranked card to finish with highest
        same_suit = [c for c in cards if c[1] == current_suit]

        if same_suit:
            return max(same_suit, key=lambda c: self.rank_strength[c[0]])
        return min(cards, key=lambda c: self.rank_strength[c[0]])



class RationalZeroOrderplayer(ZeroOrderPlayer):
    """Tries to win by playing the lowest ranked card that is higher than the incoming card of the same suit. Play lowest card otherwise."""
    def take_turn(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        trick: list[ToepPlay],
    ) -> str:
        self.hand_strength = sum(self.rank_strength[r] for r, _ in cards)
        # leading, play lowest
        if current_suit is None:
            return min(cards, key=lambda c: self.rank_strength[c[0]])
        same_suit = [c for c in cards if c[1] == current_suit]
        if same_suit:
            # get highest card in current trick (same suit only)
            same_suit_plays = [p for p in trick if p.suit == current_suit]
            if same_suit_plays:
                highest = max(
                    same_suit_plays,
                    key=lambda x: self.rank_strength[x.rank],
                )
                winning_cards = [
                    c
                    for c in same_suit
                    if self.rank_strength[c[0]] > self.rank_strength[highest.rank]
                ]
                if winning_cards:
                    return min(winning_cards, key=lambda c: self.rank_strength[c[0]])
            return min(same_suit, key=lambda c: self.rank_strength[c[0]])
        # cannot follow suit
        return min(cards, key=lambda c: self.rank_strength[c[0]])
