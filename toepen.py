# For simplicity, this version of toepen ends the game when the final card is played,
# not when the final card is played after 15 rounds as is customary.
# |
# This version also lets player 0 start, and lets the winner of the previous round start the next round
# In actual toepen, the starting player gets rotated throughout the game, in turn. # THIS HAS NOW BEEN FIXED

import random


class ToepPlay:
    # Might be redundant as all plays are just tuple[str, str]
    def __init__(self, rank: str, suit: str, player_id: int) -> None:
        self.rank = rank
        self.suit = suit
        self.player_id = player_id

    def __str__(self) -> str:
        return f"({self.rank}, {self.suit}) played by {self.player_id}"


class ToepPlayer:
    def start_game(self, identifier: int, cards: tuple[str], rank_strength):
        pass

    def take_turn(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        trick: list[ToepPlay]
    ) -> str:  # type: ignore
        # Here, current_rank will be the suit played by the previous opponent, or the rank the ToMx agent wants to play if he starts.
        pass

    def observe_play(
        self,
        cards: tuple[str, str],
        player_count: int,
        current_suit: str,
        player_id: int,
        previous_play: ToepPlay,
        lead_suit: str,
        trick_before_play: list[ToepPlay]
    ) -> None:
        pass

    def call_toep(
        self, cards: tuple[str, str], ante: int, lead_suit: str | None
    ) -> str | None:
        pass

    def respond_to_toep(
        self,
        cards: tuple[str, str],
        ante: int,
    ) -> str:  # type: ignore
        # Return either "MEEGAAN" to keep playing and up the ante, or "PASS" when one does not expect to win.
        pass

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        pass

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:  # type: ignore
        pass


class ToepController:
    SUITS = ["♠", "♣", "♥", "♦"]
    RANKS = ["J", "Q", "K", "A", "7", "8", "9", "10"]
    RANK_STRENGTH = {rank: i for i, rank in enumerate(RANKS)}

    def __init__(self):
        self._players = []

    def join(self, player):
        if player not in self._players:
            self._players.append(player)

    def _shuffle_and_divide(self):
        deck = [(rank, suit) for suit in self.SUITS for rank in self.RANKS]
        random.shuffle(deck)
        hands = []
        for i in range(len(self._players)):
            hands.append(deck[i * 4 : (i + 1) * 4])
        pile = deck[len(self._players) * 4 :]
        return hands, pile

    def _trick_winner(self, trick):
        lead_suit = trick[0].suit
        valid_cards = [play for play in trick if play.suit == lead_suit]
        winner = max(valid_cards, key=lambda x: self.RANK_STRENGTH[x.rank])
        return winner.player_id

    def _handle_toep(self, caller, hands, ante, debug):
        for p in range(len(self._players)):
            if p == caller:
                continue
            response = self._players[p].respond_to_toep(tuple(hands[p]), ante)
            if debug:
                print(f"Player {p} -> {response}")
            if response == "PASS":
                if debug:
                    print(f"Player {p} passes. Player {caller} wins {ante}")
                return caller, ante
        ante += 1
        if debug:
            print("All players meegaan. Ante =", ante)
        return None, ante

    def _handle_witte_was(self, caller, hands, pile, scores, debug):
        doubters = []
        for p in range(len(self._players)):
            if p == caller:
                continue
            response = self._players[p].respond_to_witte_was(tuple(hands[p]))
            if debug:
                print(f"Player {p} -> {response}")
            if response == "DOUBT":
                doubters.append(p)
        hand = hands[caller]
        has_witte_was = all(card[0] in ["J", "Q", "K", "A"] for card in hand)
        if not doubters:
            if debug:
                print("Everyone believes the claim.")
            if len(pile) >= 4:
                hands[caller] = pile[:4]
                del pile[:4]
            return
        if not has_witte_was:
            if debug:
                print("False witte was! Caller gets penalty.")
            scores[caller] += 1
            if len(pile) >= 4:
                hands[caller] = pile[:4]
                del pile[:4]
            return
        if has_witte_was:
            if debug:
                print("Correct witte was! Doubters get penalty.")
            for p in doubters:
                scores[p] += 1
            if len(pile) >= 4:
                hands[caller] = pile[:4]
                del pile[:4]

    def play(self, *, game_index=0, debug=False):
        hands, pile = self._shuffle_and_divide()
        for i, player in enumerate(self._players):
            player.start_game(
                i, tuple(hands[i]), self.RANK_STRENGTH
            )  # Now pass the rank strenght of hand at the start of game.
        scores = [0] * len(self._players)
        for player_id, player in enumerate(self._players):
            action = player.call_witte_was(tuple(hands[player_id]))
            if action == "WITTE_WAS":
                if debug:
                    print(f"Player {player_id} claims WITTE WAS")
                self._handle_witte_was(player_id, hands, pile, scores, debug)
        starting_player = game_index % len(self._players)
        ante = 1
        winner = None
        for trick_number in range(4):
            trick = []
            lead_suit = None
            if debug:
                print("\n--- TRICK", trick_number + 1, "---")
            for i in range(len(self._players)):
                player_id = (starting_player + i) % len(self._players)
                if debug:
                    print("\n--- TURN ---")
                    for pid, hand in enumerate(hands):
                        print(f"Player {pid} hand:", sorted(hand))
                    print("Current trick:", [str(p) for p in trick])
                    print("Lead suit:", lead_suit)
                    print("Current player:", player_id)
                action = self._players[player_id].call_toep(
                    tuple(hands[player_id]), ante, lead_suit
                )
                if action == "TOEP":
                    if debug:
                        print(f"Player {player_id} calls TOEP")
                    result, ante = self._handle_toep(player_id, hands, ante, debug)
                    if result is not None:
                        return result
                card = self._players[player_id].take_turn(
                    tuple(hands[player_id]), len(self._players), lead_suit, trick
                )
                if card not in hands[player_id]:
                    raise ValueError("Illegal card played")
                rank, suit = card
                if lead_suit is not None:
                    player_suits = [c[1] for c in hands[player_id]]
                    if lead_suit in player_suits and suit != lead_suit:
                        raise ValueError(f"Player {player_id} failed to follow suit")
                hands[player_id].remove(card)
                if lead_suit is None:
                    lead_suit = suit
                play = ToepPlay(rank, suit, player_id)
                trick_before_play = trick.copy()
                trick.append(play)
                if debug:
                    print(play)
                for p in range(len(self._players)):
                    self._players[p].observe_play(
                        tuple(hands[p]), len(self._players), lead_suit, player_id, play, lead_suit, trick_before_play
                    )
            winner = self._trick_winner(trick)
            starting_player = winner
            if debug:
                print("Trick winner:", winner)
        if debug:
            print("\nGame winner:", winner, "wins", ante)
        return winner

    def repeated_games(self, number_of_games, *, win_score=1):
        scores = [0 for _ in range(len(self._players))]
        for _ in range(number_of_games):
            winner = self.play(game_index=_, debug=False)
            scores[winner] += win_score  # type: ignore
        return scores
