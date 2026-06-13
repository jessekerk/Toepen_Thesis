from matplotlib.colors import LinearSegmentedColormap

from firstorderplayer import (
    FirstOrderPlayerVsOptimistic,
    FirstOrderPlayerVsPessimistic,
    FirstOrderPlayerVsRational,
)
from randomplayer import RandomPlayer
from secondorderplayer import (
    SecondOrderPlayerVsFirstOrderOptimistic,
    SecondOrderPlayerVsFirstOrderPessimistic,
    SecondOrderPlayerVsFirstOrderRational,
)
from toepen import ToepController
from zeroorderplayer import (
    OptimisticZeroOrderPlayer,
    PessimisticZeroOrderPlayer,
    RationalZeroOrderplayer,
)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


MODELS = {
    "Random": RandomPlayer,
    "ZO Optimistic": OptimisticZeroOrderPlayer,
    "ZO Pessimistic": PessimisticZeroOrderPlayer,
    "ZO Rational": RationalZeroOrderplayer,
    "FO vs Optimistic": FirstOrderPlayerVsOptimistic,
    "FO vs Pessimistic": FirstOrderPlayerVsPessimistic,
    "FO vs Rational": FirstOrderPlayerVsRational,
    "SO vs FO Optimistic": SecondOrderPlayerVsFirstOrderOptimistic,
    "SO vs FO Pessimistic": SecondOrderPlayerVsFirstOrderPessimistic,
    "SO vs FO Rational": SecondOrderPlayerVsFirstOrderRational,
}


def extract_row_player_score(result):
    """
    Converts controller.repeated_games(...) output into one numeric value.

    Expected case:
        result = [player_1_score, player_2_score]

    The row player is always joined first, so we return result[0].
    """

    if isinstance(result, list):
        return result[0]

    if isinstance(result, tuple):
        return result[0]

    if isinstance(result, dict):
        # Change this key if your repeated_games() returns a different dictionary.
        return result["player_1_score"]

    return result


def is_tom2_model(model_name):
    """
    Checks whether the model is a second-order ToM model.
    """

    return model_name.startswith("SO")


def add_tom2_toep_counter(player, model_name):
    """
    Adds a Toep counter only to ToM2 models.

    The counter increases whenever call_toep(...) returns "TOEP".
    """

    player.toep_count = 0

    if not is_tom2_model(model_name):
        return player

    original_call_toep = player.call_toep

    def counted_call_toep(cards, ante, lead_suit):
        result = original_call_toep(cards, ante, lead_suit)

        if result == "TOEP":
            player.toep_count += 1

        return result

    player.call_toep = counted_call_toep

    return player


def run_match(player_name, player_cls, opponent_name, opponent_cls, n_games=10000):
    """
    Runs one matchup.

    player_cls = row player
    opponent_cls = column player

    Returns:
        row_player_score: score used for the heatmap
        tom2_toep_count: number of ToM2 Toep calls in this matchup
    """

    controller = ToepController()

    row_player = add_tom2_toep_counter(
        player_cls(),
        player_name,
    )

    column_player = add_tom2_toep_counter(
        opponent_cls(),
        opponent_name,
    )

    controller.join(row_player)
    controller.join(column_player)

    result = controller.repeated_games(n_games)

    row_player_score = extract_row_player_score(result)

    tom2_toep_count = 0

    if is_tom2_model(player_name):
        tom2_toep_count += row_player.toep_count

    if is_tom2_model(opponent_name):
        tom2_toep_count += column_player.toep_count

    return row_player_score, tom2_toep_count


def run_experiment(n_games=10000):
    """
    Runs every model against every other model.

    Returns a 10 x 10 pandas DataFrame.
    """

    results = pd.DataFrame(
        index=MODELS.keys(),
        columns=MODELS.keys(),
        dtype=float,
    )

    total_tom2_toeps = 0

    for player_name, player_cls in MODELS.items():
        for opponent_name, opponent_cls in MODELS.items():
            print(f"Running {player_name} vs {opponent_name}")

            score, tom2_toep_count = run_match(
                player_name=player_name,
                player_cls=player_cls,
                opponent_name=opponent_name,
                opponent_cls=opponent_cls,
                n_games=n_games,
            )

            results.loc[player_name, opponent_name] = score
            total_tom2_toeps += tom2_toep_count

    print(f"\nTotal ToM2 Toep calls: {total_tom2_toeps}")

    return results


def plot_heatmap(results, n_games):
    """
    Plots the performance heatmap.

    Low scores are blue.
    Scores around 0.50 are white.
    High scores are green.
    """

    win_rates = results / n_games

    plt.figure(figsize=(14, 10))

    blue_white_green = LinearSegmentedColormap.from_list(
        "blue_white_green",
        [
            (0.00, "#08306B"),  # dark blue
            (0.25, "#6BAED6"),  # light blue
            (0.50, "#FFFFFF"),  # white
            (0.75, "#74C476"),  # light green
            (1.00, "#006D2C"),  # dark green
        ],
    )

    sns.heatmap(
        win_rates,
        annot=True,
        fmt=".2f",
        cmap=blue_white_green,
        vmin=0,
        vmax=1,
        center=0.50,
        linewidths=0.5,
    )

    plt.title(f"ToM Model Performance Heatmap ({n_games} games per matchup)")
    plt.xlabel("Opponent")
    plt.ylabel("Player")

    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    N_GAMES = 10000

    results = run_experiment(n_games=N_GAMES)

    print("\nFinal results:")
    print(results)

    results.to_csv("tom_heatmap_results.csv")
    print("\nSaved results to tom_heatmap_results.csv")

    plot_heatmap(results, n_games=N_GAMES)
