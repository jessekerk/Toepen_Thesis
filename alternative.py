from toepen import ToepPlay, ToepPlayer


class FirstOrderPlayerVsOptimistic(ToepPlayer):
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

        # Step 1: uniform prior over all 28 cards you do not hold
        prior = 1 / len(unknown_cards)  # 1/28 at the start of game.
        self.opp_card_probs = {card: prior for card in unknown_cards}
        self.hand_strength = sum(rank_strength[rank] for rank, _ in cards)

        # Optional: cards that are already publicly played
        self.seen_cards = set()
        self.opp_hand_strength = 0.0
        self.opp_cards_remaining = 4

    def _renormalize_opp_probs(self):
        total = sum(self.opp_card_probs.values())
        if total <= 0:
            return
        for card in self.opp_card_probs:
            self.opp_card_probs[card] /= total

    def _recompute_opp_hand_strength(self):
        expected_single_card_strength = sum(
            self.rank_strength[rank] * prob
            for (rank, suit), prob in self.opp_card_probs.items()
        )
        self.opp_hand_strength = (
            self.opp_cards_remaining * expected_single_card_strength
        )

    def _compute_hand_strength(self, cards):
        return sum(self.rank_strength[r] for r, _ in cards)

    def _expected_strength_by_suit(self):
        suit_strength = {"♠": 0.0, "♣": 0.0, "♥": 0.0, "♦": 0.0}
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
        # Only update beliefs from opponent actions
        if player_id == self.identifier:
            return

        played_card = (previous_play.rank, previous_play.suit)
        self.seen_cards.add(played_card)

        # A played card cannot still be in opponent's hand
        if played_card in self.opp_card_probs:
            self.opp_card_probs[played_card] = 0.0

        # Case 1: opponent failed to follow suit
        # Then, under normal Toepen rules, they have no cards of the lead suit.
        if lead_suit is not None and previous_play.suit != lead_suit:
            for card in list(self.opp_card_probs.keys()):
                rank, suit = card
                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        # Case 2: opponent did follow suit
        # Since this is an optimistic ToM0, he always plays the highest card
        # available in the requested suit.
        # So any higher card of that same suit is impossible.
        else:
            played_strength = self.rank_strength[previous_play.rank]
            played_suit = previous_play.suit

            for card in list(self.opp_card_probs.keys()):
                rank, suit = card
                if (
                    suit == played_suit and self.rank_strength[rank] > played_strength
                ):  # The > makes it work for optimistic agents.
                    self.opp_card_probs[card] = 0.0

        # Remove any cards that are already publicly seen from the belief table
        for card in self.seen_cards:
            if card in self.opp_card_probs:
                self.opp_card_probs[card] = 0.0

        # Step 3: normalize
        self._renormalize_opp_probs()

        # Keep a summary statistic for later Toep decisions

        self.opp_cards_remaining -= 1
        self._recompute_opp_hand_strength()
        # print(f"Opponent hand probabilities: {self.opp_card_probs}, Opponent hand strength: {self.opp_hand_strength} (Approximations), Own hand strength: {(self._compute_hand_strength(cards))} \n")

    def call_toep(
        self, cards: tuple[str, str], ante: int, lead_suit: str | None
    ) -> str | None:
        my_strength = self._compute_hand_strength(cards)

        if (
            my_strength >= self.opp_hand_strength
        ):  # could do self.opp_hand_strengh + x later for error margin...
            return "TOEP"
        return None

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return "PASS"

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        face_cards = {"J", "Q", "K", "A"}
        if len(cards) == 4 and all(rank in face_cards for rank, _ in cards):
            return "WITTE_WAS"
        return "NONE"

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


class FirstOrderPlayerVsPessimistic(ToepPlayer):
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

        # Belief over opponent's possible cards
        prior = 1 / len(unknown_cards)
        self.opp_card_probs = {card: prior for card in unknown_cards}

        self.seen_cards = set()
        self.opp_void_suits = set()
        self.opp_cards_remaining = 4

        self.hand_strength = self._compute_hand_strength(cards)
        self.opp_hand_strength = 0.0
        self._recompute_opp_hand_strength()

    def _compute_hand_strength(self, cards):
        return sum(self.rank_strength[r] for r, _ in cards)

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

        # Pessimistic player tends to preserve stronger cards
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

        # Opponent failed to follow suit -> they are void in lead_suit
        if lead_suit is not None and previous_play.suit != lead_suit:
            self.opp_void_suits.add(lead_suit)
            for card in list(self.opp_card_probs.keys()):
                _, suit = card
                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        # Opponent followed suit.
        # PessimisticZeroOrderPlayer plays the LOWEST legal card in suit.
        # Therefore any lower card in that same suit is impossible.
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
        self, cards: tuple[str, str], ante: int, lead_suit: str | None
    ) -> str | None:
        my_strength = self._compute_hand_strength(cards)

        # Be conservative, especially against a player that preserves strength
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

    def take_turn(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        trick: list[ToepPlay],
    ) -> str:
        self.hand_strength = self._compute_hand_strength(cards)
        if current_suit is None:
            return min(cards, key=lambda c: self.rank_strength[c[0]])
        same_suit = [c for c in cards if c[1] == current_suit]
        if same_suit:
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
        # Cannot follow suit: dump lowest
        return min(cards, key=lambda c: self.rank_strength[c[0]])


class FirstOrderPlayerVsRational(ToepPlayer):
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
        return sum(self.rank_strength[r] for r, _ in cards)

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

    def observe_play(  # type: ignore
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

        # Case 1: opponent failed to follow suit
        # Then they cannot hold any cards of the lead suit.
        if lead_suit is not None and previous_play.suit != lead_suit:
            for card in list(self.opp_card_probs.keys()):
                _, suit = card
                if suit == lead_suit:
                    self.opp_card_probs[card] = 0.0

        # Case 2: opponent followed suit
        else:
            played_suit = previous_play.suit
            played_strength = self.rank_strength[previous_play.rank]

            # Cards already in the trick before this play, restricted to the lead suit
            prior_same_suit_plays = []
            if lead_suit is not None:
                prior_same_suit_plays = [
                    p for p in trick_before_play if p.suit == lead_suit
                ]

            # If no earlier same-suit card exists, opponent is leading.
            # A RationalZeroOrderplayer then plays the lowest card available.
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
                    key=lambda p: self.rank_strength[p.rank],
                )
                threshold_strength = self.rank_strength[highest_prior.rank]

                # Opponent played a winning card
                if played_strength > threshold_strength:
                    # Rational player chooses the lowest same-suit card that still wins.
                    # Therefore, any same-suit card that also would have won but is lower
                    # than the played card is impossible.
                    for card in list(self.opp_card_probs.keys()):
                        rank, suit = card
                        strength = self.rank_strength[rank]
                        if suit != played_suit:
                            continue
                        if threshold_strength < strength < played_strength:
                            self.opp_card_probs[card] = 0.0

                # Opponent followed suit but did not win
                else:
                    # Then they had no same-suit card that could beat the threshold,
                    # and since RationalZeroOrderplayer plays the lowest losing card,
                    # any lower same-suit card is impossible as well.
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
        self, cards: tuple[str, str], ante: int, lead_suit: str | None
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

    def take_turn(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        trick: list[ToepPlay],
    ) -> str:
        self.hand_strength = self._compute_hand_strength(cards)

        if current_suit is None:
            return min(cards, key=lambda c: self.rank_strength[c[0]])

        same_suit = [c for c in cards if c[1] == current_suit]
        if same_suit:
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

        return min(cards, key=lambda c: self.rank_strength[c[0]])
