import random

from toepen import ToepPlay, ToepPlayer
from zeroorderplayer import (
    OptimisticZeroOrderPlayer,
    PessimisticZeroOrderPlayer,
    RationalZeroOrderplayer,
)


class SimpleFirstOrderTurnMixin:
    win_threshold = 0.50
    opponent_model_class = None

    identifier: int
    rank_strength: dict[str, int]
    opp_card_probs: dict[tuple[str, str], float]
    hand_strength: int

    def _legal_cards(self, cards, current_suit):
        if current_suit is None:
            return list(cards)

        same_suit = [card for card in cards if card[1] == current_suit]

        if same_suit:
            return same_suit

        return list(cards)

    def _lowest_card(self, cards):
        return min(cards, key=lambda card: self.rank_strength[card[0]])

    def _card_beats_current_trick(self, card, current_suit, trick):
        same_suit_plays = [play for play in trick if play.suit == current_suit]

        if not same_suit_plays:
            return False

        highest = max(
            same_suit_plays,
            key=lambda play: self.rank_strength[play.rank],
        )

        rank, suit = card

        if suit != current_suit:
            return False

        return self.rank_strength[rank] > self.rank_strength[highest.rank]

    def _my_card_beats_opp_card(self, my_card, opp_card, lead_suit):
        my_rank, my_suit = my_card
        opp_rank, opp_suit = opp_card

        if my_suit == lead_suit and opp_suit != lead_suit:
            return True

        if my_suit != lead_suit and opp_suit == lead_suit:
            return False

        if my_suit == lead_suit and opp_suit == lead_suit:
            return self.rank_strength[my_rank] > self.rank_strength[opp_rank]

        return False

    def _predict_opponent_response_to_my_card(self, opp_card, my_card):
        if self.opponent_model_class is None:
            raise ValueError("opponent_model_class must be set in the ToM1 class")

        opponent = self.opponent_model_class()

        opponent.start_game(
            -1,
            (opp_card,),
            self.rank_strength,
        )

        predicted_trick = [ToepPlay(my_card[0], my_card[1], self.identifier)]

        return opponent.take_turn(
            (opp_card,),
            2,
            my_card[1],
            predicted_trick,
        )

    def _win_probability_for_card_when_leading(self, my_card):
        win_probability = 0.0

        for opp_card, opp_card_probability in self.opp_card_probs.items():
            if opp_card_probability <= 0:
                continue

            predicted_opp_card = self._predict_opponent_response_to_my_card(
                opp_card,
                my_card,
            )

            if self._my_card_beats_opp_card(
                my_card,
                predicted_opp_card,
                my_card[1],
            ):
                win_probability += opp_card_probability

        return win_probability

    def _win_probability_for_card_when_responding(
        self,
        my_card,
        current_suit,
        trick,
    ):
        if self._card_beats_current_trick(my_card, current_suit, trick):
            return 1.0

        return 0.0

    def _win_probability_for_card(self, my_card, current_suit, trick):
        if current_suit is None:
            return self._win_probability_for_card_when_leading(my_card)

        return self._win_probability_for_card_when_responding(
            my_card,
            current_suit,
            trick,
        )

    def _choose_card_using_threshold(self, legal_cards, current_suit, trick):
        best_probability = -1.0
        best_cards = []

        for card in legal_cards:
            win_probability = self._win_probability_for_card(
                card,
                current_suit,
                trick,
            )

            if win_probability > best_probability:
                best_probability = win_probability
                best_cards = [card]

            elif win_probability == best_probability:
                best_cards.append(card)

        if best_probability >= self.win_threshold:
            return random.choice(best_cards)

        return self._lowest_card(legal_cards)

    def take_turn(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        trick: list[ToepPlay],
    ) -> str:  # type: ignore
        self.hand_strength = self._compute_hand_strength(cards)  # type: ignore

        legal_cards = self._legal_cards(cards, current_suit)

        return self._choose_card_using_threshold(
            legal_cards,
            current_suit,
            trick,
        )


class FirstOrderPlayerVsOptimistic(SimpleFirstOrderTurnMixin, ToepPlayer):
    opponent_model_class = OptimisticZeroOrderPlayer
    win_threshold = 0.50

    def start_game(self, identifier: int, cards: tuple[str], rank_strength):
        self.identifier = identifier
        self.rank_strength = rank_strength

        self.all_cards = [
            (rank, suit)
            for suit in ["♠", "♣", "♥", "♦"]
            for rank in ["J", "Q", "K", "A", "7", "8", "9", "10"]
        ]

        self.my_initial_cards = set(cards)

        unknown_cards = [
            card for card in self.all_cards if card not in self.my_initial_cards
        ]

        prior = 1 / len(unknown_cards)

        self.opp_card_probs = {card: prior for card in unknown_cards}

        self.hand_strength = self._compute_hand_strength(cards)
        self.seen_cards = set()
        self.opp_hand_strength = 0.0
        self.opp_cards_remaining = 4

        self._recompute_opp_hand_strength()

    def _renormalize_opp_probs(self):
        total = sum(self.opp_card_probs.values())

        if total <= 0:
            return

        for card in self.opp_card_probs:
            self.opp_card_probs[card] /= total

    def _recompute_opp_hand_strength(self):
        expected_single_card_strength = sum(
            self.rank_strength[rank] * prob
            for (rank, _), prob in self.opp_card_probs.items()
        )

        self.opp_hand_strength = (
            self.opp_cards_remaining * expected_single_card_strength
        )

    def _compute_hand_strength(self, cards):
        return sum(self.rank_strength[rank] for rank, _ in cards)

    def _expected_strength_by_suit(self):
        suit_strength = {
            "♠": 0.0,
            "♣": 0.0,
            "♥": 0.0,
            "♦": 0.0,
        }

        for (rank, suit), prob in self.opp_card_probs.items():
            suit_strength[suit] += self.rank_strength[rank] * prob

        return suit_strength

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
        if player_id == self.identifier:
            return

        played_card = (previous_play.rank, previous_play.suit)
        self.seen_cards.add(played_card)

        if played_card in self.opp_card_probs:
            self.opp_card_probs[played_card] = 0.0

        if lead_suit is not None and previous_play.suit != lead_suit:
            for card in list(self.opp_card_probs.keys()):
                _, suit = card

                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        else:
            played_strength = self.rank_strength[previous_play.rank]
            played_suit = previous_play.suit

            for card in list(self.opp_card_probs.keys()):
                rank, suit = card

                if suit == played_suit and self.rank_strength[rank] > played_strength:
                    self.opp_card_probs[card] = 0.0

        for card in self.seen_cards:
            if card in self.opp_card_probs:
                self.opp_card_probs[card] = 0.0

        self._renormalize_opp_probs()

        self.opp_cards_remaining = max(0, self.opp_cards_remaining - 1)
        self._recompute_opp_hand_strength()

    def call_toep(
        self,
        cards: tuple[str, str],
        ante: int,
        lead_suit: str | None,
    ) -> str | None:
        my_strength = self._compute_hand_strength(cards)

        if my_strength >= self.opp_hand_strength:
            return "TOEP"

        return None

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return "PASS"

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        face_cards = {"J", "Q", "K", "A"}

        if len(cards) == 4 and all(rank in face_cards for rank, _ in cards):
            return "WITTE_WAS"

        return "NONE"

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:
        return "BELIEVE"


class FirstOrderPlayerVsPessimistic(SimpleFirstOrderTurnMixin, ToepPlayer):
    opponent_model_class = PessimisticZeroOrderPlayer
    win_threshold = 0.50

    def start_game(self, identifier: int, cards: tuple[str], rank_strength):
        self.identifier = identifier
        self.rank_strength = rank_strength

        self.all_cards = [
            (rank, suit)
            for suit in ["♠", "♣", "♥", "♦"]
            for rank in ["J", "Q", "K", "A", "7", "8", "9", "10"]
        ]

        self.my_initial_cards = set(cards)

        unknown_cards = [
            card for card in self.all_cards if card not in self.my_initial_cards
        ]

        prior = 1 / len(unknown_cards)

        self.opp_card_probs = {card: prior for card in unknown_cards}

        self.seen_cards = set()
        self.opp_void_suits = set()
        self.opp_cards_remaining = 4

        self.hand_strength = self._compute_hand_strength(cards)
        self.opp_hand_strength = 0.0

        self._recompute_opp_hand_strength()

    def _compute_hand_strength(self, cards):
        return sum(self.rank_strength[rank] for rank, _ in cards)

    def _renormalize_opp_probs(self):
        total = sum(self.opp_card_probs.values())

        if total <= 0:
            return

        for card in self.opp_card_probs:
            self.opp_card_probs[card] /= total

    def _recompute_opp_hand_strength(self):
        weighted_cards = [
            (self.rank_strength[rank], prob)
            for (rank, _), prob in self.opp_card_probs.items()
            if prob > 0
        ]

        if not weighted_cards or self.opp_cards_remaining <= 0:
            self.opp_hand_strength = 0.0
            return

        avg_strength = sum(strength * prob for strength, prob in weighted_cards)

        self.opp_hand_strength = self.opp_cards_remaining * (avg_strength + 1.5)

    def _remove_seen_cards(self):
        for card in self.seen_cards:
            if card in self.opp_card_probs:
                self.opp_card_probs[card] = 0.0

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
        if player_id == self.identifier:
            return

        played_card = (previous_play.rank, previous_play.suit)
        self.seen_cards.add(played_card)

        if played_card in self.opp_card_probs:
            self.opp_card_probs[played_card] = 0.0

        if lead_suit is not None and previous_play.suit != lead_suit:
            self.opp_void_suits.add(lead_suit)

            for card in list(self.opp_card_probs.keys()):
                _, suit = card

                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        else:
            played_strength = self.rank_strength[previous_play.rank]
            played_suit = previous_play.suit

            for card in list(self.opp_card_probs.keys()):
                rank, suit = card

                if suit == played_suit and self.rank_strength[rank] < played_strength:
                    self.opp_card_probs[card] = 0.0

        self._remove_seen_cards()
        self._renormalize_opp_probs()

        self.opp_cards_remaining = max(0, self.opp_cards_remaining - 1)
        self._recompute_opp_hand_strength()

    def call_toep(
        self,
        cards: tuple[str, str],
        ante: int,
        lead_suit: str | None,
    ) -> str | None:
        my_strength = self._compute_hand_strength(cards)

        if lead_suit is not None:
            return None

        if my_strength >= self.opp_hand_strength + 8:
            return "TOEP"

        return None

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return "PASS"

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        face_cards = {"J", "Q", "K", "A"}

        if len(cards) == 4 and all(rank in face_cards for rank, _ in cards):
            return "WITTE_WAS"

        return "NONE"

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:
        return "BELIEVE"


class FirstOrderPlayerVsRational(SimpleFirstOrderTurnMixin, ToepPlayer):
    opponent_model_class = RationalZeroOrderplayer
    win_threshold = 0.50

    def start_game(self, identifier: int, cards: tuple[str], rank_strength):
        self.identifier = identifier
        self.rank_strength = rank_strength

        self.all_cards = [
            (rank, suit)
            for suit in ["♠", "♣", "♥", "♦"]
            for rank in ["J", "Q", "K", "A", "7", "8", "9", "10"]
        ]

        self.my_initial_cards = set(cards)

        unknown_cards = [
            card for card in self.all_cards if card not in self.my_initial_cards
        ]

        prior = 1 / len(unknown_cards)

        self.opp_card_probs = {card: prior for card in unknown_cards}

        self.seen_cards = set()
        self.opp_cards_remaining = 4

        self.hand_strength = self._compute_hand_strength(cards)
        self.opp_hand_strength = 0.0

        self._recompute_opp_hand_strength()

    def _compute_hand_strength(self, cards):
        return sum(self.rank_strength[rank] for rank, _ in cards)

    def _renormalize_opp_probs(self):
        total = sum(self.opp_card_probs.values())

        if total <= 0:
            return

        for card in self.opp_card_probs:
            self.opp_card_probs[card] /= total

    def _recompute_opp_hand_strength(self):
        expected_single_card_strength = sum(
            self.rank_strength[rank] * prob
            for (rank, _), prob in self.opp_card_probs.items()
        )

        self.opp_hand_strength = (
            self.opp_cards_remaining * expected_single_card_strength
        )

    def _remove_seen_cards(self):
        for card in self.seen_cards:
            if card in self.opp_card_probs:
                self.opp_card_probs[card] = 0.0

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
        if player_id == self.identifier:
            return

        played_card = (previous_play.rank, previous_play.suit)
        self.seen_cards.add(played_card)

        if played_card in self.opp_card_probs:
            self.opp_card_probs[played_card] = 0.0

        if lead_suit is not None and previous_play.suit != lead_suit:
            for card in list(self.opp_card_probs.keys()):
                _, suit = card

                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        else:
            played_suit = previous_play.suit
            played_strength = self.rank_strength[previous_play.rank]

            prior_same_suit_plays = []

            if lead_suit is not None:
                prior_same_suit_plays = [
                    play for play in trick_before_play if play.suit == lead_suit
                ]

            if not prior_same_suit_plays:
                for card in list(self.opp_card_probs.keys()):
                    rank, suit = card

                    if (
                        suit == played_suit
                        and self.rank_strength[rank] < played_strength
                    ):
                        self.opp_card_probs[card] = 0.0

            else:
                highest_prior = max(
                    prior_same_suit_plays,
                    key=lambda play: self.rank_strength[play.rank],
                )

                threshold_strength = self.rank_strength[highest_prior.rank]

                if played_strength > threshold_strength:
                    for card in list(self.opp_card_probs.keys()):
                        rank, suit = card
                        strength = self.rank_strength[rank]

                        if suit != played_suit:
                            continue

                        if threshold_strength < strength < played_strength:
                            self.opp_card_probs[card] = 0.0

                else:
                    for card in list(self.opp_card_probs.keys()):
                        rank, suit = card
                        strength = self.rank_strength[rank]

                        if suit != played_suit:
                            continue

                        if strength < played_strength:
                            self.opp_card_probs[card] = 0.0

                        if strength > threshold_strength:
                            self.opp_card_probs[card] = 0.0

        self._remove_seen_cards()
        self._renormalize_opp_probs()

        self.opp_cards_remaining = max(0, self.opp_cards_remaining - 1)
        self._recompute_opp_hand_strength()

    def call_toep(
        self,
        cards: tuple[str, str],
        ante: int,
        lead_suit: str | None,
    ) -> str | None:
        my_strength = self._compute_hand_strength(cards)

        if lead_suit is not None:
            return None

        if my_strength >= self.opp_hand_strength + 4:
            return "TOEP"

        return None

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return "PASS"

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        face_cards = {"J", "Q", "K", "A"}

        if len(cards) == 4 and all(rank in face_cards for rank, _ in cards):
            return "WITTE_WAS"

        return "NONE"

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:
        return "BELIEVE"
