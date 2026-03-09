"""
Unit tests for state management
"""

import pytest
from datetime import datetime
from app.state import AgentState, Phase


class TestAgentState:
    """Test cases for AgentState class"""

    def test_initial_state(self):
        """Test that agent starts in Init state"""
        state = AgentState()
        assert state.phase == Phase.Init
        assert state.destination is None
        assert state.dates is None
        assert state.card is None
        assert state.tools_called == []

    def test_state_advancement(self):
        """Test state machine advancement"""
        state = AgentState()

        # Test Init -> ClarifyRequirements
        state.advance()
        assert state.phase == Phase.ClarifyRequirements

        # Test ClarifyRequirements -> PlanTools
        state.advance()
        assert state.phase == Phase.PlanTools

        # Test PlanTools -> ExecuteTools
        state.advance()
        assert state.phase == Phase.ExecuteTools

        # Test ExecuteTools -> AnalyzeResults
        state.advance()
        assert state.phase == Phase.AnalyzeResults

        # Test AnalyzeResults -> ResolveIssues
        state.advance()
        assert state.phase == Phase.ResolveIssues

        # Test ResolveIssues -> ProduceStructuredOutput
        state.advance()
        assert state.phase == Phase.ProduceStructuredOutput

        # Test ProduceStructuredOutput -> Done
        state.advance()
        assert state.phase == Phase.Done

    def test_state_data_assignment(self):
        """Test that state data can be assigned"""
        state = AgentState()

        state.destination = "Paris"
        state.dates = "2026-06-01 to 2026-06-08"
        state.card = "BankGold"

        assert state.destination == "Paris"
        assert state.dates == "2026-06-01 to 2026-06-08"
        assert state.card == "BankGold"

    def test_tools_called_tracking(self):
        """Test that tools called are tracked"""
        state = AgentState()

        state.tools_called.append("weather")
        state.tools_called.append("fx")

        assert "weather" in state.tools_called
        assert "fx" in state.tools_called
        assert len(state.tools_called) == 2

    def test_state_reset(self):
        """Test that state can be reset using reset method"""
        state = AgentState()

        # Advance and set data
        state.advance()
        state.destination = "Tokyo"
        state.tools_called.append("weather")

        # Reset using the reset method
        state.reset()

        assert state.phase == Phase.Init
        assert state.destination is None
        assert state.tools_called == []

    def test_phase_enum_values(self):
        """Test that Phase enum has expected values"""
        # Test that core phases exist and are in order
        phases = list(Phase)
        # 8 core phases + 7 enhanced phases = 15 total
        assert len(phases) >= 8  # At least 8 core phases

        # Verify core phases exist
        assert Phase.Init in phases
        assert Phase.ClarifyRequirements in phases
        assert Phase.PlanTools in phases
        assert Phase.ExecuteTools in phases
        assert Phase.AnalyzeResults in phases
        assert Phase.ResolveIssues in phases
        assert Phase.ProduceStructuredOutput in phases
        assert Phase.Done in phases


class TestEnhancedAgentState:
    """Test cases for enhanced AgentState class"""

    def test_initial_state_enhanced(self):
        """Test that agent starts with enhanced state tracking"""
        state = AgentState()
        assert state.phase == Phase.Init
        assert state.created_at is not None
        assert state.updated_at is not None
        assert state.tools_called == []
        assert state.successful_tools == []
        assert state.failed_tools == []
        assert state.transition_history == []
        assert state.current_error is None
        assert state.clarification_needed is None
        assert state.validation_results == {}
        assert state.metadata == {}

    def test_tool_success_tracking(self):
        """Test tool success tracking"""
        state = AgentState()

        # Mark tools as successful
        state.mark_tool_success("weather")
        state.mark_tool_success("fx")

        assert len(state.tools_called) == 2
        assert "weather" in state.tools_called
        assert "fx" in state.tools_called
        assert "weather" in state.successful_tools
        assert "fx" in state.successful_tools

    def test_tool_error_handling(self):
        """Test tool error handling and tracking"""
        state = AgentState()
        state.advance()  # Move to ClarifyRequirements
        state.advance()  # Move to PlanTools
        state.advance()  # Move to ExecuteTools

        # Handle a tool error
        state.handle_tool_error("search", "API timeout", "ToolExecutionError")

        assert state.phase == Phase.HANDLING_TOOL_ERROR
        assert state.current_error is not None
        assert state.current_error.failed_tool == "search"
        assert state.current_error.error_message == "API timeout"
        assert "search" in state.failed_tools

    def test_clarification_request(self):
        """Test clarification request functionality"""
        state = AgentState()
        state.advance()  # Move to ClarifyRequirements

        # Request clarification
        state.request_clarification("What is your destination?")

        assert state.phase == Phase.AWAITING_USER_CLARIFICATION
        assert state.clarification_needed == "What is your destination?"

    def test_provide_clarification(self):
        """Test providing clarification"""
        state = AgentState()
        state.advance()  # Move to ClarifyRequirements
        state.request_clarification("What is your destination?")

        # Provide clarification
        state.provide_clarification("Paris")

        assert state.phase == Phase.ClarifyRequirements
        assert state.clarification_needed is None
        assert state.metadata.get("last_clarification") == "Paris"

    def test_validation_results(self):
        """Test validation results handling"""
        state = AgentState()
        state.advance()  # ClarifyRequirements
        state.advance()  # PlanTools
        state.advance()  # ExecuteTools
        state.advance()  # AnalyzeResults
        state.advance()  # ResolveIssues

        # All validations pass - now in ResolveIssues, can transition to ProduceStructuredOutput
        result = state.validate_tool_results({"weather": True, "fx": True})

        assert result is True
        assert state.phase == Phase.ProduceStructuredOutput
        assert state.validation_results == {"weather": True, "fx": True}

    def test_validation_failure(self):
        """Test validation failure handling"""
        state = AgentState()
        state.advance()  # ClarifyRequirements
        state.advance()  # PlanTools
        state.advance()  # ExecuteTools
        state.advance()  # AnalyzeResults
        state.advance()  # ResolveIssues

        # Some validations fail - from ResolveIssues, can go to RETRYING_TOOLS
        result = state.validate_tool_results({"weather": True, "search": False})

        assert result is False
        assert state.phase == Phase.RETRYING_TOOLS

    def test_state_summary(self):
        """Test comprehensive state summary"""
        state = AgentState()
        state.destination = "Paris"
        state.mark_tool_success("weather")

        summary = state.get_state_summary()

        assert "current_phase" in summary
        assert "destination" in summary
        assert "tools_called" in summary
        assert "successful_tools" in summary
        assert "failed_tools" in summary
        assert "has_error" in summary
        assert "created_at" in summary
        assert "updated_at" in summary
        assert summary["destination"] == "Paris"
        assert "weather" in summary["tools_called"]

    def test_state_completion_checks(self):
        """Test state completion and status checks"""
        state = AgentState()

        # Initially not in error state
        assert not state.is_in_error_state()
        assert not state.is_awaiting_user()
        assert state.can_proceed()

        # After reaching Done (through 8 core phases)
        state.advance()  # ClarifyRequirements
        state.advance()  # PlanTools
        state.advance()  # ExecuteTools
        state.advance()  # AnalyzeResults
        state.advance()  # ResolveIssues
        state.advance()  # ProduceStructuredOutput
        state.advance()  # Done

        assert state.phase == Phase.Done
        assert not state.can_proceed()  # Done is a blocking state

    def test_enhanced_state_advancement(self):
        """Test enhanced state machine advancement through core phases"""
        state = AgentState()

        # Test core workflow progression
        core_phases = [
            Phase.Init,
            Phase.ClarifyRequirements,
            Phase.PlanTools,
            Phase.ExecuteTools,
            Phase.AnalyzeResults,
            Phase.ResolveIssues,
            Phase.ProduceStructuredOutput,
            Phase.Done
        ]

        # Verify initial state
        assert state.phase == Phase.Init

        # Advance through all core phases
        for i in range(1, len(core_phases)):
            can_advance = state.advance()
            if i < len(core_phases) - 1:
                assert can_advance
            assert state.phase == core_phases[i]

        # Final state should be Done
        assert state.phase == Phase.Done
    
    def test_state_reset_enhanced(self):
        """Test enhanced state reset functionality"""
        state = AgentState()

        # Populate state with data
        state.destination = "Paris"
        state.mark_tool_success("weather")
        state.advance()
        state.advance()

        # Reset state
        state.reset()

        # Should be back to initial state
        assert state.phase == Phase.Init
        assert state.destination is None
        assert state.tools_called == []
        assert state.successful_tools == []
        assert state.failed_tools == []

    def test_error_retry_logic(self):
        """Test error retry logic"""
        state = AgentState()
        state.advance()  # ClarifyRequirements
        state.advance()  # PlanTools
        state.advance()  # ExecuteTools

        # Handle error
        state.handle_tool_error("search", "timeout")

        assert state.current_error.can_retry()
        assert state.current_error.retry_count == 0

        # Simulate retries
        state.current_error.retry_count = 3
        assert not state.current_error.can_retry()

    def test_transition_history(self):
        """Test transition history tracking"""
        state = AgentState()

        state.advance()
        state.advance()

        history = state.get_transition_history()

        assert len(history) == 2
        assert history[0]["from"] == "Init"
        assert history[0]["to"] == "ClarifyRequirements"
        assert history[1]["from"] == "ClarifyRequirements"
        assert history[1]["to"] == "PlanTools"
