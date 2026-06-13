import random

from toepen import ToepPlayer


class RandomPlayer(ToepPlayer):
    def take_turn(self, cards, player_count, lead_suit, trick) -> str:  # type: ignore
        if lead_suit is None:
            return random.choice(cards)

        same_suit = [c for c in cards if c[1] == lead_suit]

        if same_suit:
            return random.choice(same_suit)
        return random.choice(cards)

    def respond_to_toep(self, cards: tuple[str, str], ante: int) -> str:
        return random.choice(["MEEGAAN", "PASS"])

    def call_toep(self, cards: tuple[str, str], ante: int, lead_suit) -> str | None:
        if random.random() < 0.1:
            return "TOEP"
        return None

    def respond_to_witte_was(self, cards: tuple[str, str]) -> str:
        return random.choice(["DOUBT", "BELIEVE"])

    def call_witte_was(self, cards: tuple[str, str]) -> str | None:
        if random.random() <= 0.1:
            return "WITTE_WAS"
        return None


# p_4_face_cards = math.comb(16, 4) / math.comb(32, 4)   #Probability of pulling 4 face cards out of the 16 total face cards out of the 32 total cards in the pile. ()
