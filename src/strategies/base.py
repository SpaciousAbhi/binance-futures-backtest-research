from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies.
    All strategies must implement the get_signal and set_params methods.
    """
    def __init__(self, name: str, hypothesis: str, params: dict = None):
        self.name = name
        self.hypothesis = hypothesis
        self.params = params if params is not None else {}

    @abstractmethod
    def get_signal(self, df: pd.DataFrame, i: int, live_metrics: dict = None) -> dict:
        """
        Evaluates the historical data up to index i (closed candle).
        Returns None or a dictionary with details for execution:
        {
            "side": "Long" or "Short",
            "stop_loss": float,
            "take_profit": float,
            "reason": str
        }
        """
        pass

    def set_params(self, params: dict):
        """Updates strategy parameters."""
        self.params.update(params)

    @abstractmethod
    def get_param_grid(self) -> dict:
        """Returns the dictionary of parameter lists to scan during grid search."""
        pass
