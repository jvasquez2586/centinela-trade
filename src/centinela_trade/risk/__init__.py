"""Risk management: position sizing, limits and circuit breakers (spec §4).

Every order goes through ``RiskManager.validate()`` with no bypass (spec RISK-10).
"""
