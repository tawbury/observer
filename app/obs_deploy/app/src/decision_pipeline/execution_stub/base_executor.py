"""
Base executor class for decision execution.

Provides common functionality shared by all executor implementations.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from shared.serialization import order_hint_fingerprint

from decision_pipeline.contracts.order_decision import OrderDecision
from decision_pipeline.contracts.execution_hint import ExecutionHint

from .execution_context import ExecutionContext
from .execution_mode import ExecutionMode
from .execution_result import ExecutionResult, ExecutionStatus
from .iexecution import IExecution


__all__ = ["BaseExecutor", "extract_decision_id"]

log = logging.getLogger("BaseExecutor")


def extract_decision_id(order: Any) -> str:
    """
    Extract decision ID from order object.

    Args:
        order: Order object

    Returns:
        Decision ID string or "UNKNOWN"
    """
    # Try common attribute names
    for attr in ["decision_id", "id", "order_id"]:
        value = getattr(order, attr, None)
        if value is not None:
            return str(value)

    # Try dictionary access
    if isinstance(order, dict):
        for key in ["decision_id", "id", "order_id"]:
            if key in order:
                return str(order[key])

    return "UNKNOWN"


class BaseExecutor(IExecution, ABC):
    """
    Abstract base class for executors.

    Provides common functionality:
    - Decision ID extraction
    - Fingerprint generation
    - Result construction
    - Error handling
    - Execution counting

    Subclasses must implement:
    - _do_execute(): Actual execution logic
    """

    def __init__(self, mode: ExecutionMode):
        """
        Initialize base executor.

        Args:
            mode: Execution mode for this executor
        """
        self._mode = mode
        self._execution_count = 0

    @property
    def mode(self) -> ExecutionMode:
        """Get execution mode."""
        return self._mode

    @property
    def execution_count(self) -> int:
        """Get total number of executions."""
        return self._execution_count

    def execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute an order with context.

        Template method that:
        1. Increments execution count
        2. Extracts decision ID
        3. Generates fingerprint
        4. Calls subclass implementation
        5. Handles errors

        Args:
            order: Order to execute
            hint: Execution hint/context
            context: Execution context

        Returns:
            ExecutionResult with status and details
        """
        self._execution_count += 1

        # Extract decision ID
        decision_id = extract_decision_id(order)

        # Generate fingerprint
        fp = order_hint_fingerprint(order, hint)

        try:
            # Call subclass implementation
            result = self._do_execute(
                order=order,
                hint=hint,
                context=context,
                decision_id=decision_id,
                fingerprint=fp,
            )
            return result

        except Exception as e:
            log.error(f"Execution failed for decision {decision_id}: {e}")
            return self._create_error_result(
                decision_id=decision_id,
                fingerprint=fp,
                error=str(e),
            )

    @abstractmethod
    def _do_execute(
        self,
        *,
        order: OrderDecision,
        hint: ExecutionHint,
        context: ExecutionContext,
        decision_id: str,
        fingerprint: str,
    ) -> ExecutionResult:
        """
        Perform the actual execution.

        Subclasses implement this to define execution behavior.

        Args:
            order: Order to execute
            hint: Execution hint
            context: Execution context
            decision_id: Extracted decision ID
            fingerprint: Order/hint fingerprint

        Returns:
            ExecutionResult with status and details
        """
        pass

    def _create_error_result(
        self,
        decision_id: str,
        fingerprint: str,
        error: str,
    ) -> ExecutionResult:
        """
        Create an error ExecutionResult.

        Args:
            decision_id: Decision ID
            fingerprint: Order/hint fingerprint
            error: Error message

        Returns:
            ExecutionResult with ERROR status
        """
        return ExecutionResult(
            mode=self._mode.value,
            status=ExecutionStatus.ERROR.value,
            decision_id=decision_id,
            fingerprint=fingerprint,
            reason=error,
            audit={
                "error": error,
                "execution_count": self._execution_count,
            },
        )
