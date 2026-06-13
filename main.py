from randomplayer import RandomPlayer

from firstorderplayer import (  # noqa: F401
    FirstOrderPlayerVsOptimistic,  # noqa
    FirstOrderPlayerVsPessimistic,  # noqa
    FirstOrderPlayerVsRational,  # noqa
)
from randomplayer import RandomPlayer  # noqa: F401
from secondorderplayer import (  # noqa
    SecondOrderPlayerVsFirstOrderOptimistic,
    SecondOrderPlayerVsFirstOrderPessimistic,
    SecondOrderPlayerVsFirstOrderRational,
)
from toepen import ToepController
from zeroorderplayer import (  # noqa: F401
    OptimisticZeroOrderPlayer,
    PessimisticZeroOrderPlayer,
    RationalZeroOrderplayer,
)

controller = ToepController()
controller.join(FirstOrderPlayerVsOptimistic())
controller.join(OptimisticZeroOrderPlayer())
controller.play(debug=True)
print(controller.repeated_games(1000))
