"""
priority_engine_cli.py

CLI nástroj pro prioritizaci úkolů:
- Eisenhower kvadranty (urgent/important)
- Vrstvy (Fundament / Strategic / Support / Leisure)
- Skórování (Impact, Leverage, Effort, UrgencyMultiplier)
- Štítky (HighROI, BigBet, QuickWin)
- Výběr denních MIT

Návrh je OOP a řídí se SOLID:
- S (Single Responsibility): každá třída má jasný účel (repozitař, politika urgence, klasifikátor, skórovací strategie…)
- O (Open/Closed): klíčové části (skórování, politika urgence) jsou rozšiřitelné přes rozhraní
- L (Liskov Substitution): abstraktní rozhraní lze nahradit implementacemi
- I (Interface Segregation): malá, specifická rozhraní (např. ScoringStrategy)
- D (Dependency Inversion): vysokoúrovňové služby závisí na abstrakcích, ne na konkrétních třídách

"""

__all__ = ["__version__"]
__version__ = "0.2.1"