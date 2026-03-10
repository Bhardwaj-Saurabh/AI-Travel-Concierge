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

    Basic Workflow (8 core phases):
    Init → ClarifyRequirements → PlanTools → ExecuteTools → AnalyzeResults → ResolveIssues → ProduceStructuredOutput → Done

    With Enhanced States:
    - AWAITING_USER_CLARIFICATION: When agent needs more input
    - HANDLING_TOOL_ERROR: When a tool call fails
    - RETRYING_TOOLS: Attempting failed tool calls again
    - ESCALATING_ERROR: Critical error requiring user intervention
    """

    # Core 8-phase workflow (as per specification)
    Init = "Init"
    ClarifyRequirements = "ClarifyRequirements"
    PlanTools = "PlanTools"
    ExecuteTools = "ExecuteTools"
    AnalyzeResults = "AnalyzeResults"
    ResolveIssues = "ResolveIssues"
    ProduceStructuredOutput = "ProduceStructuredOutput"
    Done = "Done"

    # Granular enhancement phases
    AWAITING_USER_CLARIFICATION = "AwaitingUserClarification"
    HANDLING_TOOL_ERROR = "HandlingToolError"
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
    - Granular state tracking with 8 core phases
    - State transition history
    - Error handling and recovery
    - Requirements and clarification management
    - Tool call tracking with results and errors
    - Analysis results and data completeness
    - Issue tracking and resolution
    - Structured output and citation management
    - Validation checks before transitions
    - Conditional transitions
    """

    # Phase descriptions for each core phase
    PHASE_DESCRIPTIONS = {
        Phase.Init: "Initialize session and capture user goal",
        Phase.ClarifyRequirements: "Ask targeted questions to gather required information",
        Phase.PlanTools: "Decide which tools to call and with what parameters",
        Phase.ExecuteTools: "Execute planned tools and collect results",
        Phase.AnalyzeResults: "Process tool outputs and validate data completeness",
        Phase.ResolveIssues: "Handle any problems or edge cases identified",
        Phase.ProduceStructuredOutput: "Generate Pydantic-validated JSON and natural language summary",
        Phase.Done: "Process complete",
    }

    def __init__(self):
        """Initialize agent state with granular tracking."""
        import uuid

        # Session identifier
        self.session_id: str = str(uuid.uuid4())

        # Core state
        self.phase = Phase.Init
        self.destination: Optional[str] = None
        self.dates: Optional[str] = None
        self.card: Optional[str] = None

        # Requirements management
        self.requirements: Dict[str, Any] = {}
        self.required_fields: List[str] = []
        self.clarification_questions: List[str] = []

        # Tool tracking
        self.tools_called: List[str] = []
        self.tool_results: Dict[str, Any] = {}
        self.tool_errors: Dict[str, str] = {}

        # Analysis and completeness
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.data_completeness: float = 0.0
        self.validation_errors: List[str] = []

        # Issue management
        self.issues: List[str] = []
        self.resolution_attempts: List[str] = []
        self.resolved_issues: List[str] = []

        # Structured output
        self.structured_output: Optional[Dict[str, Any]] = None
        self.natural_language_summary: Optional[str] = None
        self.citations: List[str] = []

        # Context and metadata
        self.context: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        # Enhanced tracking
        self.transition_history: List[StateTransition] = []
        self.current_error: Optional[ErrorContext] = None
        self.clarification_needed: Optional[str] = None
        self.validation_results: Dict[str, bool] = {}

        # Track which tools succeeded/failed
        self.successful_tools: List[str] = []
        self.failed_tools: List[str] = []

        # Timestamps
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def advance(self, reason: str = "Normal progression", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Advance to the next phase in the workflow with validation.

        Args:
            reason: Reason for the transition
            metadata: Additional metadata about the transition

        Returns:
            True if transition was successful, False if at terminal state
        """
        # Determine next phase based on current phase and conditions
        next_phase = self._determine_next_phase()

        if next_phase:
            self._transition_to(next_phase, reason, metadata or {})
            return True
        return False

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

        # Normal workflow progression through 8 core phases
        phase_transitions = {
            Phase.Init: Phase.ClarifyRequirements,
            Phase.ClarifyRequirements: Phase.PlanTools,
            Phase.PlanTools: Phase.ExecuteTools,
            Phase.ExecuteTools: Phase.AnalyzeResults,
            Phase.AnalyzeResults: Phase.ResolveIssues,
            Phase.ResolveIssues: Phase.ProduceStructuredOutput,
            Phase.ProduceStructuredOutput: Phase.Done,
            Phase.RETRYING_TOOLS: Phase.ExecuteTools,
            Phase.AWAITING_USER_CLARIFICATION: Phase.ClarifyRequirements,
            Phase.CHECKING_AVAILABILITY: Phase.PlanTools,
            Phase.TRANSLATING_CONTENT: Phase.ProduceStructuredOutput,
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

        # Print state transition for console output evidence
        print(f"[STATE] State Transition: {old_phase.value} -> {new_phase.value} | Reason: {reason}")

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
            Phase.ExecuteTools: [Phase.AnalyzeResults, Phase.HANDLING_TOOL_ERROR],
            Phase.AnalyzeResults: [Phase.ResolveIssues],
            Phase.ResolveIssues: [Phase.ProduceStructuredOutput, Phase.RETRYING_TOOLS],
            Phase.ProduceStructuredOutput: [Phase.Done, Phase.TRANSLATING_CONTENT],
            Phase.RETRYING_TOOLS: [Phase.ExecuteTools, Phase.ESCALATING_ERROR],
            Phase.HANDLING_TOOL_ERROR: [Phase.RETRYING_TOOLS, Phase.ESCALATING_ERROR],
            Phase.AWAITING_USER_CLARIFICATION: [Phase.ClarifyRequirements],
            Phase.CHECKING_AVAILABILITY: [Phase.PlanTools, Phase.SCHEDULING_EVENT],
            Phase.TRANSLATING_CONTENT: [Phase.ProduceStructuredOutput],
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
                Phase.ProduceStructuredOutput,
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

    # --- Requirements management ---

    def set_requirements(self, requirements: Dict[str, Any]):
        """Set travel requirements."""
        self.requirements = requirements
        import time
        time.sleep(0.001)  # Ensure updated_at differs from created_at
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_clarification_question(self, question: str):
        """Add a clarification question (deduplicates)."""
        if question not in self.clarification_questions:
            self.clarification_questions.append(question)

    def mark_requirement_clarified(self, field: str):
        """Mark a required field as clarified."""
        if field in self.required_fields:
            self.required_fields.remove(field)

    # --- Tool call tracking ---

    def add_tool_call(self, tool_name: str, result: Any = None, error: str = None):
        """
        Record a tool call with its result and/or error.

        Args:
            tool_name: Name of the tool
            result: Result from the tool (if successful)
            error: Error message (if failed)
        """
        if tool_name not in self.tools_called:
            self.tools_called.append(tool_name)
        if result is not None:
            self.tool_results[tool_name] = result
        if error is not None:
            self.tool_errors[tool_name] = error

    # --- Analysis and completeness ---

    def set_analysis_results(self, results: Dict[str, Any]):
        """Set analysis results and recalculate data completeness."""
        self.analysis_results = results
        self._calculate_data_completeness()
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def _calculate_data_completeness(self):
        """Calculate data completeness based on required fields."""
        if not self.required_fields:
            self.data_completeness = 1.0
            return
        filled = sum(1 for f in self.required_fields if f in self.requirements)
        self.data_completeness = filled / len(self.required_fields)

    def is_data_complete(self, threshold: float = 0.8) -> bool:
        """Check if data completeness meets threshold."""
        return self.data_completeness >= threshold

    # --- Issue management ---

    def add_issue(self, issue: str):
        """Add an issue to track."""
        self.issues.append(issue)

    def has_issues(self) -> bool:
        """Check if there are unresolved issues."""
        return len(self.issues) > 0

    def add_resolution_attempt(self, attempt: str):
        """Record an attempt to resolve an issue."""
        self.resolution_attempts.append(attempt)

    def resolve_issue(self, issue: str):
        """Move an issue from unresolved to resolved."""
        if issue in self.issues:
            self.issues.remove(issue)
            self.resolved_issues.append(issue)

    # --- Structured output ---

    def set_structured_output(self, output: Dict[str, Any], summary: str):
        """Set the structured output and natural language summary."""
        self.structured_output = output
        self.natural_language_summary = summary

    def add_citation(self, citation: str):
        """Add a citation (deduplicates)."""
        if citation not in self.citations:
            self.citations.append(citation)

    # --- Phase descriptions ---

    def get_phase_description(self) -> str:
        """Get description for the current phase."""
        return self.PHASE_DESCRIPTIONS.get(self.phase, self.phase.value)

    # --- Status summary ---

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary."""
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "phase_description": self.get_phase_description(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "requirements": self.requirements,
            "tools_called": self.tools_called,
            "issues": self.issues,
            "data_completeness": self.data_completeness,
            "has_structured_output": self.structured_output is not None,
            "citations_count": len(self.citations),
        }

    def is_complete(self) -> bool:
        """Check if the agent has reached the Done phase."""
        return self.phase == Phase.Done

    def reset(self):
        """Reset the state to initial values for a new session."""
        import uuid

        # Keep transition history for debugging
        self.transition_history.append(
            StateTransition(
                from_phase=self.phase,
                to_phase=Phase.Init,
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason="Manual reset"
            )
        )

        self.session_id = str(uuid.uuid4())
        self.phase = Phase.Init
        self.destination = None
        self.dates = None
        self.card = None
        self.requirements = {}
        self.required_fields = []
        self.clarification_questions = []
        self.tools_called = []
        self.tool_results = {}
        self.tool_errors = {}
        self.analysis_results = None
        self.data_completeness = 0.0
        self.validation_errors = []
        self.issues = []
        self.resolution_attempts = []
        self.resolved_issues = []
        self.structured_output = None
        self.natural_language_summary = None
        self.citations = []
        self.context = {}
        self.metadata = {}
        self.successful_tools = []
        self.failed_tools = []
        self.current_error = None
        self.clarification_needed = None
        self.validation_results = {}
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()

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
