class PowerScoringStrategy:
    """
    Scoring strategy based on a power-law formula.

    The score is computed as:

    .. math::

        P = \\frac{ImportanceCore \\times UM}{Effort^{\\alpha}}

    where :math:`\\alpha` is a tunable parameter controlling the
    penalization of effort.

    :param alpha: Exponent parameter used to adjust the effect of effort
                  in the denominator. Defaults to ``0.7``.
    :type alpha: float
    """

    def __init__(self, alpha: float = 0.7) -> None:
        """
        Initialize the scoring strategy.

        :param alpha: Exponent parameter for effort penalization.
        :type alpha: float
        """
        self._alpha = alpha

    @staticmethod
    def importance_core(impact: float, leverage: float, layer_weight: float) -> float:
        """
        Compute the core importance of a task.

        The formula is a weighted combination of impact, adjusted layer weight,
        and leverage:

        .. math::

            ImportanceCore = 0.5 \\times Impact + 0.3 \\times
                             \\left(\\frac{LayerWeight \\times 5.0}{1.3}\\right)
                             + 0.2 \\times Leverage

        :param impact: The impact score of the task.
        :type impact: float
        :param leverage: The leverage score of the task.
        :type leverage: float
        :param layer_weight: Weight factor associated with the task's layer.
        :type layer_weight: float
        :return: Calculated importance core value.
        :rtype: float
        """
        return 0.5*impact + 0.3*(layer_weight*5.0/1.3) + 0.2*leverage

    def score(self, importance_core: float, um: float, effort: float) -> float:
        """
        Compute the final prioritization score.

        The score combines importance, urgency multiplier (UM), and effort:

        .. math::

            Score = \\frac{ImportanceCore \\times UM}{max(Effort, 10^{-6})^{\\alpha}}

        A small epsilon (``1e-6``) is applied to avoid division by zero.

        :param importance_core: Precomputed importance core value.
        :type importance_core: float
        :param um: Urgency multiplier.
        :type um: float
        :param effort: Effort estimate (difficulty). Must be positive.
        :type effort: float
        :return: Final score value.
        :rtype: float
        """
        eff = max(1e-6, effort)
        return (importance_core * um) / (eff ** self._alpha)
