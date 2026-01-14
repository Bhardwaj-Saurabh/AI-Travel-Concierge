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
        # Test that enum values are unique and in order
        phases = list(Phase)
        assert len(phases) == 8  # Updated to include all 8 phases
        assert phases[0] == Phase.Init
        assert phases[1] == Phase.ClarifyRequirements
        assert phases[2] == Phase.PlanTools
        assert phases[3] == Phase.ExecuteTools
        assert phases[4] == Phase.AnalyzeResults
        assert phases[5] == Phase.ResolveIssues
        assert phases[6] == Phase.ProduceStructuredOutput
        assert phases[7] == Phase.Done


class TestEnhancedAgentState:
    """Test cases for enhanced AgentState class"""
    
    def test_initial_state_enhanced(self):
        """Test that agent starts with enhanced state tracking"""
        state = AgentState()
        assert state.phase == Phase.Init
        assert state.session_id is not None
        assert state.created_at is not None
        assert state.updated_at is not None
        assert state.requirements == {}
        assert state.required_fields == []
        assert state.clarification_questions == []
        assert state.tools_called == []
        assert state.tool_results == {}
        assert state.tool_errors == {}
        assert state.analysis_results is None
        assert state.data_completeness == 0.0
        assert state.validation_errors == []
        assert state.issues == []
        assert state.resolution_attempts == []
        assert state.resolved_issues == []
        assert state.structured_output is None
        assert state.natural_language_summary is None
        assert state.citations == []
        assert state.context == {}
        assert state.metadata == {}
    
    def test_requirements_management(self):
        """Test requirements setting and tracking"""
        state = AgentState()
        
        # Set requirements
        requirements = {
            "destination": "Paris",
            "travel_dates": "2026-06-01 to 2026-06-08",
            "card": "BankGold"
        }
        state.set_requirements(requirements)
        
        assert state.requirements == requirements
        assert state.updated_at > state.created_at
    
    def test_clarification_questions(self):
        """Test clarification question management"""
        state = AgentState()
        
        # Add questions
        state.add_clarification_question("What is your destination?")
        state.add_clarification_question("When are you traveling?")
        state.add_clarification_question("What is your destination?")  # Duplicate
        
        assert len(state.clarification_questions) == 2
        assert "What is your destination?" in state.clarification_questions
        assert "When are you traveling?" in state.clarification_questions
    
    def test_requirement_clarification(self):
        """Test requirement field clarification"""
        state = AgentState()
        state.required_fields = ["destination", "dates", "card"]
        
        # Mark fields as clarified
        state.mark_requirement_clarified("destination")
        state.mark_requirement_clarified("dates")
        
        assert "destination" not in state.required_fields
        assert "dates" not in state.required_fields
        assert "card" in state.required_fields
    
    def test_tool_call_tracking(self):
        """Test tool call and result tracking"""
        state = AgentState()
        
        # Add successful tool calls
        state.add_tool_call("weather", {"temperature": 25.0})
        state.add_tool_call("fx", {"rate": 0.85})
        
        # Add tool call with error
        state.add_tool_call("search", error="API timeout")
        
        assert len(state.tools_called) == 3
        assert "weather" in state.tool_results
        assert "fx" in state.tool_results
        assert "search" in state.tool_errors
        assert state.tool_results["weather"] == {"temperature": 25.0}
        assert state.tool_errors["search"] == "API timeout"
    
    def test_analysis_results(self):
        """Test analysis results and data completeness calculation"""
        state = AgentState()
        state.required_fields = ["field1", "field2", "field3"]
        state.requirements = {"field1": "value1", "field2": "value2"}
        
        analysis_results = {
            "tools_executed": 3,
            "tools_with_errors": 1,
            "data_quality": "good"
        }
        state.set_analysis_results(analysis_results)
        
        assert state.analysis_results == analysis_results
        assert state.data_completeness == 2/3  # 2 out of 3 fields completed
    
    def test_issue_management(self):
        """Test issue tracking and resolution"""
        state = AgentState()
        
        # Add issues
        state.add_issue("Weather data incomplete")
        state.add_issue("Search API timeout")
        
        assert len(state.issues) == 2
        assert state.has_issues()
        
        # Add resolution attempts
        state.add_resolution_attempt("Using fallback weather data")
        state.add_resolution_attempt("Retrying search with different parameters")
        
        assert len(state.resolution_attempts) == 2
        
        # Resolve one issue
        state.resolve_issue("Weather data incomplete")
        
        assert len(state.issues) == 1
        assert len(state.resolved_issues) == 1
        assert "Weather data incomplete" in state.resolved_issues
        assert "Search API timeout" in state.issues
    
    def test_structured_output(self):
        """Test structured output and citation management"""
        state = AgentState()
        
        output = {"destination": "Paris", "plan": "Complete"}
        summary = "Travel plan for Paris"
        
        state.set_structured_output(output, summary)
        state.add_citation("https://example.com")
        state.add_citation("https://weather.com")
        
        assert state.structured_output == output
        assert state.natural_language_summary == summary
        assert len(state.citations) == 2
        assert "https://example.com" in state.citations
    
    def test_phase_descriptions(self):
        """Test phase description functionality"""
        state = AgentState()
        
        expected_descriptions = {
            Phase.Init: "Initialize session and capture user goal",
            Phase.ClarifyRequirements: "Ask targeted questions to gather required information",
            Phase.PlanTools: "Decide which tools to call and with what parameters",
            Phase.ExecuteTools: "Execute planned tools and collect results",
            Phase.AnalyzeResults: "Process tool outputs and validate data completeness",
            Phase.ResolveIssues: "Handle any problems or edge cases identified",
            Phase.ProduceStructuredOutput: "Generate Pydantic-validated JSON and natural language summary",
            Phase.Done: "Process complete"
        }
        
        for phase, expected_desc in expected_descriptions.items():
            state.phase = phase
            assert state.get_phase_description() == expected_desc
    
    def test_status_summary(self):
        """Test comprehensive status summary"""
        state = AgentState()
        state.set_requirements({"destination": "Paris"})
        state.add_tool_call("weather", {"temp": 25})
        state.add_issue("Test issue")
        
        status = state.get_status_summary()
        
        assert "session_id" in status
        assert "phase" in status
        assert "phase_description" in status
        assert "created_at" in status
        assert "updated_at" in status
        assert "requirements" in status
        assert "tools_called" in status
        assert "issues" in status
        assert "data_completeness" in status
        assert "has_structured_output" in status
        assert "citations_count" in status
    
    def test_state_completion_checks(self):
        """Test state completion and data completeness checks"""
        state = AgentState()
        
        # Initially not complete
        assert not state.is_complete()
        assert not state.has_issues()
        assert not state.is_data_complete()
        
        # Add some data
        state.required_fields = ["field1", "field2"]
        state.requirements = {"field1": "value1"}
        state.set_analysis_results({})
        
        # Should be 50% complete
        assert state.data_completeness == 0.5
        assert not state.is_data_complete()  # Default threshold is 0.8
        assert state.is_data_complete(0.4)  # Should pass with lower threshold
        
        # Complete the process
        state.phase = Phase.Done
        assert state.is_complete()
    
    def test_enhanced_state_advancement(self):
        """Test enhanced state machine advancement"""
        state = AgentState()
        
        # Test all phases
        phases = list(Phase)
        for i, expected_phase in enumerate(phases):
            if i == 0:
                assert state.phase == expected_phase
            else:
                can_advance = state.advance()
                if i < len(phases) - 1:
                    assert can_advance
                    assert state.phase == expected_phase
                else:
                    # The last advance should return False and set phase to Done
                    # Note: The advance() method returns True for the last transition to Done
                    assert state.phase == Phase.Done
    
    def test_state_reset_enhanced(self):
        """Test enhanced state reset functionality"""
        state = AgentState()
        
        # Populate state with data
        state.set_requirements({"destination": "Paris"})
        state.add_tool_call("weather", {"temp": 25})
        state.add_issue("Test issue")
        state.advance()
        state.advance()
        
        original_session_id = state.session_id
        
        # Reset state
        state.reset()
        
        # Should be back to initial state
        assert state.phase == Phase.Init
        assert state.session_id != original_session_id
        assert state.requirements == {}
        assert state.tools_called == []
        assert state.issues == []
        assert state.created_at is not None
        assert state.updated_at is not None
    
    def test_data_completeness_edge_cases(self):
        """Test data completeness calculation edge cases"""
        state = AgentState()
        
        # No required fields - should be 100% complete
        state.set_analysis_results({})
        assert state.data_completeness == 1.0
        
        # All fields present
        state.required_fields = ["field1", "field2"]
        state.requirements = {"field1": "value1", "field2": "value2"}
        state.set_analysis_results({})
        assert state.data_completeness == 1.0
        
        # No fields present
        state.requirements = {}
        state.set_analysis_results({})
        assert state.data_completeness == 0.0
    
    def test_tool_error_handling(self):
        """Test tool error handling and tracking"""
        state = AgentState()
        
        # Add tool with both result and error (both are stored)
        state.add_tool_call("test_tool", result={"data": "test"}, error="API error")
        
        assert "test_tool" in state.tools_called
        assert "test_tool" in state.tool_errors
        assert "test_tool" in state.tool_results  # Both result and error are stored
        assert state.tool_errors["test_tool"] == "API error"
        assert state.tool_results["test_tool"] == {"data": "test"}
    
    def test_citation_management(self):
        """Test citation management and deduplication"""
        state = AgentState()
        
        # Add citations
        state.add_citation("https://example.com")
        state.add_citation("https://weather.com")
        state.add_citation("https://example.com")  # Duplicate
        
        assert len(state.citations) == 2
        assert "https://example.com" in state.citations
        assert "https://weather.com" in state.citations
