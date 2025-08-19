class PowerScoringStrategy:
    """P = (ImportanceCore * UM) / (Effort ** alpha)"""
    def __init__(self, alpha: float = 0.7) -> None:
        self._alpha = alpha
    @staticmethod
    def importance_core(impact: float, leverage: float, layer_weight: float) -> float:
        return 0.5*impact + 0.3*(layer_weight*5.0/1.3) + 0.2*leverage
    def score(self, importance_core: float, um: float, effort: float) -> float:
        eff = max(1e-6, effort)
        return (importance_core * um) / (eff ** self._alpha)
