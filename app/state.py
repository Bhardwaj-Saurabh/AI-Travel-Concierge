# app/state.py
"""
Enhanced Agent State Management

This module provides sophisticated state management for the AI Travel Concierge agent,
including granular states, error handling, and state transition validation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field


class Phase(Enum):
    """
    Granular agent execution phases with error handling and clarification states.

    Basic Workflow:
    Init → ClarifyRequirements → PlanTools → ExecuteTools → Synthesize → Done

    With Enhanced States:
    - AWAITING_USER_CLARIFICATION: When agent needs more input
    - HANDLING_TOOL_ERROR: When a tool call fails
    - VALIDATING_RESULTS: Checking tool outputs before synthesis
    - RETRYING_TOOLS: Attempting failed tool calls again
    - ESCALATING_ERROR: Critical error requiring user intervention
    """

    # Core workflow phases
    Init = "Init"
    ClarifyRequirements = "ClarifyRequirements"
    PlanTools = "PlanTools"
    ExecuteTools = "ExecuteTools"
    Synthesize = "Synthesize"
    Done = "Done"

    # Granular enhancement phases
    AWAITING_USER_CLARIFICATION = "AwaitingUserClarification"
    HANDLING_TOOL_ERROR = "HandlingToolError"
    VALIDATING_RESULTS = "ValidatingResults"
    RETRYING_TOOLS = "RetryingTools"
    ESCALATING_ERROR = "EscalatingError"

    # Additional workflow phases
    CHECKING_AVAILABILITY = "CheckingAvailability"
    TRANSLATING_CONTENT = "TranslatingContent"
    SCHEDULING_EVENT = "SchedulingEvent"


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_phase: Phase
    to_phase: Phase
    timestamp: str
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorContext:
    """Context about an error that occurred."""
    error_type: str
    error_message: str
    failed_tool: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def can_retry(self) -> bool:
        """Check if error can be retried."""
        return self.retry_count < self.max_retries


class AgentState:
    """
    Enhanced agent state management with granular phases and error handling.

    Features:
    - Granular state tracking
    - State transition history
    - Error handling and recovery
    - Validation checks before transitions
    - State rollback capability
    - Conditional transitions
    """

    def __init__(self):
        """Initialize agent state with granular tracking."""
        # Core state
        self.phase = Phase.Init
        self.destination: Optional[str] = None
        self.dates: Optional[str] = None
        self.card: Optional[str] = None
        self.tools_called: List[str] = []

        # Enhanced tracking
        self.transition_history: List[StateTransition] = []
        self.current_error: Optional[ErrorContext] = None
        self.clarification_needed: Optional[str] = None
        self.validation_results: Dict[str, bool] = {}
        self.metadata: Dict[str, Any] = {}

        # Track which tools succeeded/failed
        self.successful_tools: List[str] = []
        self.failed_tools: List[str] = []

        # Timestamps
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def advance(self, reason: str = "Normal progression", metadata: Optional[Dict[str, Any]] = None):
        """
        Advance to the next phase in the workflow with validation.

        Args:
            reason: Reason for the transition
            metadata: Additional metadata about the transition
        """
        # Determine next phase based on current phase and conditions
        next_phase = self._determine_next_phase()

        if next_phase:
            self._transition_to(next_phase, reason, metadata or {})

    def _determine_next_phase(self) -> Optional[Phase]:
        """
        Determine the next phase based on current state and conditions.

        Returns:
            Next phase to transition to, or None if at terminal state
        """
        # If in error state, handle error first
        if self.current_error and self.current_error.can_retry():
            return Phase.RETRYING_TOOLS
        elif self.current_error and not self.current_error.can_retry():
            return Phase.ESCALATING_ERROR

        # If clarification is needed
        if self.clarification_needed:
            return Phase.AWAITING_USER_CLARIFICATION

        # Normal workflow progression
        phase_transitions = {
            Phase.Init: Phase.ClarifyRequirements,
            Phase.ClarifyRequirements: Phase.PlanTools,
            Phase.PlanTools: Phase.ExecuteTools,
            Phase.ExecuteTools: Phase.VALIDATING_RESULTS,
            Phase.VALIDATING_RESULTS: Phase.Synthesize,
            Phase.Synthesize: Phase.Done,
            Phase.RETRYING_TOOLS: Phase.ExecuteTools,
            Phase.AWAITING_USER_CLARIFICATION: Phase.ClarifyRequirements,
            Phase.CHECKING_AVAILABILITY: Phase.PlanTools,
            Phase.TRANSLATING_CONTENT: Phase.Synthesize,
            Phase.SCHEDULING_EVENT: Phase.Done,
            Phase.HANDLING_TOOL_ERROR: Phase.RETRYING_TOOLS,
            Phase.Done: None  # Terminal state
        }

        return phase_transitions.get(self.phase)

    def _transition_to(self, new_phase: Phase, reason: str, metadata: Dict[str, Any]):
        """
        Execute state transition with validation and history tracking.

        Args:
            new_phase: Target phase
            reason: Reason for transition
            metadata: Transition metadata
        """
        # Validate transition
        if not self._can_transition_to(new_phase):
            raise ValueError(f"Invalid transition from {self.phase.value} to {new_phase.value}")

        # Record transition
        transition = StateTransition(
            from_phase=self.phase,
            to_phase=new_phase,
            timestamp=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            metadata=metadata
        )
        self.transition_history.append(transition)

        # Execute transition
        old_phase = self.phase
        self.phase = new_phase
        self.updated_at = datetime.now(timezone.utc).isoformat()

        # Clear state-specific data if needed
        if new_phase == Phase.ClarifyRequirements:
            self.clarification_needed = None
        elif new_phase == Phase.ExecuteTools:
            self.current_error = None

    def _can_transition_to(self, new_phase: Phase) -> bool:
        """
        Validate if transition to new phase is allowed.

        Args:
            new_phase: Target phase

        Returns:
            True if transition is valid
        """
        # Allow transitions from any phase to error handling phases
        error_phases = {
            Phase.HANDLING_TOOL_ERROR,
            Phase.ESCALATING_ERROR,
            Phase.AWAITING_USER_CLARIFICATION
        }
        if new_phase in error_phases:
            return True

        # Allow transition from Done to Init (reset)
        if self.phase == Phase.Done and new_phase == Phase.Init:
            return True

        # Validate normal workflow transitions
        valid_next_phases = self._get_valid_next_phases()
        return new_phase in valid_next_phases

    def _get_valid_next_phases(self) -> List[Phase]:
        """Get list of valid next phases from current phase."""
        transitions = {
            Phase.Init: [Phase.ClarifyRequirements],
            Phase.ClarifyRequirements: [Phase.PlanTools, Phase.AWAITING_USER_CLARIFICATION],
            Phase.PlanTools: [Phase.ExecuteTools, Phase.CHECKING_AVAILABILITY],
            Phase.ExecuteTools: [Phase.VALIDATING_RESULTS, Phase.HANDLING_TOOL_ERROR, Phase.Synthesize],
            Phase.VALIDATING_RESULTS: [Phase.Synthesize, Phase.RETRYING_TOOLS],
            Phase.Synthesize: [Phase.Done, Phase.TRANSLATING_CONTENT],
            Phase.RETRYING_TOOLS: [Phase.ExecuteTools, Phase.ESCALATING_ERROR],
            Phase.HANDLING_TOOL_ERROR: [Phase.RETRYING_TOOLS, Phase.ESCALATING_ERROR],
            Phase.AWAITING_USER_CLARIFICATION: [Phase.ClarifyRequirements],
            Phase.CHECKING_AVAILABILITY: [Phase.PlanTools, Phase.SCHEDULING_EVENT],
            Phase.TRANSLATING_CONTENT: [Phase.Synthesize],
            Phase.SCHEDULING_EVENT: [Phase.Done],
            Phase.ESCALATING_ERROR: [Phase.Done],
            Phase.Done: [Phase.Init]
        }
        return transitions.get(self.phase, [])

    def handle_tool_error(self, tool_name: str, error_message: str, error_type: str = "ToolExecutionError"):
        """
        Handle a tool execution error.

        Args:
            tool_name: Name of the failed tool
            error_message: Error message
            error_type: Type of error
        """
        # Create or update error context
        if self.current_error and self.current_error.failed_tool == tool_name:
            self.current_error.retry_count += 1
        else:
            self.current_error = ErrorContext(
                error_type=error_type,
                error_message=error_message,
                failed_tool=tool_name,
                retry_count=0
            )

        # Record failed tool
        if tool_name not in self.failed_tools:
            self.failed_tools.append(tool_name)

        # Transition to error handling state
        self._transition_to(
            Phase.HANDLING_TOOL_ERROR,
            f"Tool '{tool_name}' failed: {error_message}",
            {"tool": tool_name, "error": error_message}
        )

    def request_clarification(self, clarification_question: str):
        """
        Request clarification from user.

        Args:
            clarification_question: Question to ask the user
        """
        self.clarification_needed = clarification_question
        self._transition_to(
            Phase.AWAITING_USER_CLARIFICATION,
            "Need user clarification",
            {"question": clarification_question}
        )

    def provide_clarification(self, clarification_response: str):
        """
        User provides clarification.

        Args:
            clarification_response: User's response to clarification
        """
        self.metadata["last_clarification"] = clarification_response
        self.clarification_needed = None
        self._transition_to(
            Phase.ClarifyRequirements,
            "User provided clarification",
            {"response": clarification_response}
        )

    def mark_tool_success(self, tool_name: str):
        """
        Mark a tool as successfully executed.

        Args:
            tool_name: Name of the successful tool
        """
        if tool_name not in self.tools_called:
            self.tools_called.append(tool_name)
        if tool_name not in self.successful_tools:
            self.successful_tools.append(tool_name)

    def validate_tool_results(self, validation_checks: Dict[str, bool]) -> bool:
        """
        Validate tool results before proceeding to synthesis.

        Args:
            validation_checks: Dictionary of validation check results

        Returns:
            True if all validations passed
        """
        self.validation_results = validation_checks
        all_valid = all(validation_checks.values())

        if all_valid:
            self._transition_to(
                Phase.Synthesize,
                "All validations passed",
                {"validations": validation_checks}
            )
        else:
            failed_checks = [k for k, v in validation_checks.items() if not v]
            self._transition_to(
                Phase.RETRYING_TOOLS,
                f"Validation failed: {', '.join(failed_checks)}",
                {"failed_checks": failed_checks}
            )

        return all_valid

    def reset(self):
        """Reset the state to initial values while preserving history."""
        self.phase = Phase.Init
        self.destination = None
        self.dates = None
        self.card = None
        self.tools_called = []
        self.successful_tools = []
        self.failed_tools = []
        self.current_error = None
        self.clarification_needed = None
        self.validation_results = {}
        self.metadata = {}

        # Keep transition history for debugging
        self.transition_history.append(
            StateTransition(
                from_phase=self.phase,
                to_phase=Phase.Init,
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason="Manual reset"
            )
        )

    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of current state.

        Returns:
            Dictionary with state information
        """
        return {
            "current_phase": self.phase.value,
            "destination": self.destination,
            "dates": self.dates,
            "card": self.card,
            "tools_called": self.tools_called,
            "successful_tools": self.successful_tools,
            "failed_tools": self.failed_tools,
            "has_error": self.current_error is not None,
            "error_details": {
                "type": self.current_error.error_type,
                "message": self.current_error.error_message,
                "failed_tool": self.current_error.failed_tool,
                "retry_count": self.current_error.retry_count,
                "can_retry": self.current_error.can_retry()
            } if self.current_error else None,
            "needs_clarification": self.clarification_needed is not None,
            "clarification_question": self.clarification_needed,
            "validation_status": self.validation_results,
            "transition_count": len(self.transition_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def get_transition_history(self) -> List[Dict[str, Any]]:
        """
        Get state transition history.

        Returns:
            List of transition records
        """
        return [
            {
                "from": t.from_phase.value,
                "to": t.to_phase.value,
                "timestamp": t.timestamp,
                "reason": t.reason,
                "metadata": t.metadata
            }
            for t in self.transition_history
        ]

    def is_in_error_state(self) -> bool:
        """Check if agent is in an error state."""
        error_phases = {
            Phase.HANDLING_TOOL_ERROR,
            Phase.RETRYING_TOOLS,
            Phase.ESCALATING_ERROR
        }
        return self.phase in error_phases

    def is_awaiting_user(self) -> bool:
        """Check if agent is waiting for user input."""
        return self.phase == Phase.AWAITING_USER_CLARIFICATION

    def can_proceed(self) -> bool:
        """Check if agent can proceed with execution."""
        blocking_phases = {
            Phase.AWAITING_USER_CLARIFICATION,
            Phase.ESCALATING_ERROR,
            Phase.Done
        }
        return self.phase not in blocking_phases
