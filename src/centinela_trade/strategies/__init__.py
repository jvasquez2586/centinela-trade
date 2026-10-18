"""Trading strategies and their indicators (spec §3).

Strategies receive candles and their own state and emit ``Signal`` objects only;
they never create orders nor know the capital (spec STR-03).
"""
