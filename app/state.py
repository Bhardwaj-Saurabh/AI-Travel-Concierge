# app/state.py
from enum import Enum
from typing import List, Optional

class Phase(Enum):
    """Agent execution phases."""
    Init = "Init"
    ClarifyRequirements = "ClarifyRequirements"
    PlanTools = "PlanTools"
    ExecuteTools = "ExecuteTools"
    Synthesize = "Synthesize"
    Done = "Done"

class AgentState:
    """
    Manages agent execution state through the workflow phases.
    
    TODO: Implement state management functionality
    - Track current phase and transition between phases
    - Store extracted requirements (destination, dates, card)
    - Track tools called during execution
    - Provide methods to advance state and reset
    """
    
    def __init__(self):
        # TODO: Initialize state variables
        # This is a placeholder - replace with actual implementation
        self.phase = Phase.Init
        self.destination: Optional[str] = None
        self.dates: Optional[str] = None
        self.card: Optional[str] = None
        self.tools_called: List[str] = []
    
    def advance(self):
        """
        Advance to the next phase in the workflow.
        
        TODO: Implement phase advancement logic
        - Move through phases: Init → ClarifyRequirements → PlanTools → ExecuteTools → Synthesize → Done
        - Handle phase transitions appropriately
        - Log phase changes for debugging
        """
        # TODO: Implement phase advancement
        # This is a placeholder - replace with actual implementation
        pass
    
    def reset(self):
        """
        Reset the state to initial values.
        
        TODO: Implement state reset functionality
        - Reset phase to Init
        - Clear all stored data
        - Reset tools_called list
        """
        # TODO: Implement state reset
        # This is a placeholder - replace with actual implementation
        pass