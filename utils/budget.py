"""Budget management for LLM API calls."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BudgetManager:
    """Manages and enforces LLM API call budgets."""

    def __init__(self, max_calls: int = 200):
        """
        Initialize budget manager.

        Args:
            max_calls: Maximum number of LLM calls allowed
        """
        self.max_calls = max_calls
        self.calls_made = 0
        self.calls_by_type = {}
        logger.info(f"BudgetManager initialized with max_calls={max_calls}")

    def can_make_call(self, call_type: str = "default") -> bool:
        """
        Check if we can make another LLM call within budget.

        Args:
            call_type: Type of call (for tracking purposes)

        Returns:
            True if within budget, False otherwise
        """
        if self.calls_made >= self.max_calls:
            logger.warning(
                f"Budget limit reached: {self.calls_made}/{self.max_calls} calls made"
            )
            return False
        return True

    def record_call(self, call_type: str = "default", tokens_used: Optional[int] = None):
        """
        Record an LLM call.

        Args:
            call_type: Type of call (e.g., 'tone_analysis', 'readability')
            tokens_used: Number of tokens used (optional, for tracking)
        """
        self.calls_made += 1
        self.calls_by_type[call_type] = self.calls_by_type.get(call_type, 0) + 1
        logger.debug(
            f"Call recorded: type={call_type}, total={self.calls_made}/{self.max_calls}"
        )
        if tokens_used:
            logger.debug(f"Tokens used: {tokens_used}")

    def get_stats(self) -> dict:
        """
        Get budget statistics.

        Returns:
            Dictionary with budget usage stats
        """
        return {
            "total_calls": self.calls_made,
            "max_calls": self.max_calls,
            "remaining_calls": max(0, self.max_calls - self.calls_made),
            "budget_used_percent": (self.calls_made / self.max_calls * 100)
            if self.max_calls > 0
            else 0,
            "calls_by_type": self.calls_by_type.copy(),
        }

    def reset(self):
        """Reset budget counters."""
        self.calls_made = 0
        self.calls_by_type = {}
        logger.info("Budget counters reset")
