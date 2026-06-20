"""Progress tracking utilities for OracleBatchUpdater.

Provides ProgressTracker for elapsed time and ETA calculation,
ASCII progress bar rendering, and human-readable time formatting.
"""

import time
from typing import Optional


def format_eta(seconds: float) -> str:
    """Format a duration in seconds as a human-readable string.

    Examples:
        45      -> "45s"
        90      -> "1m 30s"
        3723    -> "1h 2m 3s"
        0       -> "0s"
        86400   -> "1d"
        90061   -> "1d 1h 1m 1s"

    Args:
        seconds: Duration in seconds (non-negative).

    Returns:
        A formatted string like "1h 23m 45s" or "1d 2h".
    """
    if seconds < 0:
        seconds = 0

    total_seconds = int(seconds)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_progress_bar(current: int, total: int, width: int = 30) -> str:
    """Render an ASCII progress bar.

    Examples:
        format_progress_bar(0, 100)    -> "[>                              ] 0%"
        format_progress_bar(45, 100)   -> "[============>                   ] 45%"
        format_progress_bar(100, 100)  -> "[==============================] 100%"

    Args:
        current: Current progress value.
        total: Total target value.
        width: Character width of the bar (excluding brackets).

    Returns:
        A string like "[=====>    ] 45%".
    """
    if total <= 0:
        percentage = 100
    else:
        percentage = min(int((current / total) * 100), 100)

    filled = int((percentage / 100) * width)
    if filled < 0:
        filled = 0
    if filled > width:
        filled = width

    if percentage < 100:
        bar = "=" * (filled - 1) + ">" + " " * (width - filled) if filled > 0 else ">" + " " * (width - 1)
    else:
        bar = "=" * width

    return f"[{bar}] {percentage}%"


class ProgressTracker:
    """Tracks elapsed time and calculates estimated time remaining (ETA).

    The tracker is updated by calling ``update()`` at each progress step.
    Call ``start()`` before the first update to initialise the start time.

    Usage::

        tracker = ProgressTracker()
        tracker.start()
        for i, item in enumerate(items, 1):
            process(item)
            eta = tracker.update(i, len(items))
            print(f"{tracker.format_progress_bar()}  ETA: {tracker.format_eta()}")

    Attributes:
        elapsed_seconds: Total elapsed time in seconds since ``start()``.
        eta_seconds: Estimated seconds remaining, or 0 if not yet calculable.
    """

    def __init__(self):
        self._start_time: Optional[float] = None
        self._current: int = 0
        self._total: int = 0
        self.elapsed_seconds: float = 0.0
        self.eta_seconds: float = 0.0

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def start(self):
        """Record the start time.  Call once before the first ``update()``."""
        self._start_time = time.time()
        self._current = 0
        self._total = 0
        self.elapsed_seconds = 0.0
        self.eta_seconds = 0.0

    def update(self, current: int, total: int) -> float:
        """Update progress counters and recompute ETA.

        Args:
            current: Number of items processed so far.
            total: Total number of items to process.

        Returns:
            ETA in seconds (0 if not yet computable).
        """
        self._current = current
        self._total = total

        if self._start_time is None:
            self._start_time = time.time()

        self.elapsed_seconds = time.time() - self._start_time

        if current > 0 and total > 0:
            rate = self.elapsed_seconds / current
            self.eta_seconds = rate * (total - current)
        else:
            self.eta_seconds = 0.0

        return self.eta_seconds

    def reset(self):
        """Reset all counters to their initial state."""
        self._start_time = None
        self._current = 0
        self._total = 0
        self.elapsed_seconds = 0.0
        self.eta_seconds = 0.0

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def format_eta(self) -> str:
        """Return the current ETA as a human-readable string."""
        return format_eta(self.eta_seconds)

    def format_elapsed(self) -> str:
        """Return the elapsed time as a human-readable string."""
        return format_eta(self.elapsed_seconds)

    def format_progress_bar(self, width: int = 30) -> str:
        """Return an ASCII progress bar for the current state."""
        return format_progress_bar(self._current, self._total, width)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def percentage(self) -> int:
        """Current completion percentage (0-100)."""
        if self._total <= 0:
            return 0
        return min(int((self._current / self._total) * 100), 100)

    @property
    def current(self) -> int:
        return self._current

    @property
    def total(self) -> int:
        return self._total