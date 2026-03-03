# shared pydantics contracts 
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from typing import List, Optional, Literal

# allowed action types 
class ActionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    
# action schema 
class Action(BaseModel):
    """ 
    Define a single executable UI action
    This is the only structure the model uses to control the system
    """
    action_type: ActionType = Field(..., description="Type of UI action to perform")
    target_description: str = Field(..., description="Description of the target element to perform the action on")
    text: Optional[str] = Field(default=None, description="Text to type if the action is a type action")

    @field_validator("text")
    @classmethod
    def validate_text_for_type(cls, value, info):
        """
        Ensures text is provided only for TYPE actions
        """
        action_type= info.data.get("action_type")
        if action_type == ActionType.TYPE and not value:
            raise ValueError("TYPE action must include 'text' field.")
        if action_type != ActionType.TYPE and value is not None:
            raise ValueError("Text should only be provided for TYPE actions.")
        return value
    
# agent response schema  # using model validator cause i am using contract logic 
class AgentResponse(BaseModel):
    """ 
    This is a strict contract for agent and it must adhere to this contract
    Define the response schema for the agent 
    """
    thought: str = Field(..., description="Thought process of the agent for the current UI state")
    next_action: Optional[Action]= Field(default=None, description="Next action to perform")
    confidence: float = Field(..., description="Confidence of the agent in its action")
    goal_completed: bool = Field(..., description="Whether the agent has completed its goal")

    @model_validator(mode="after")
    def validate_next_action(self):
        """
        If goal completed is false next_action must exist otherwise,
        Ensures next_action is not provided when goal_completed is True
        """
        goal_completed = self.goal_completed
        next_action = self.next_action
        if goal_completed is False and next_action is None:
            raise ValueError("Next action should be provided when goal is not completed.")
        if goal_completed is True and next_action is not None:
            raise ValueError("Next action should not be provided when goal is completed.")
        return self
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value):
        """
        Ensures confidence is between 0 and 1
        """
        if not (0 <= value <= 1):
            raise ValueError("Confidence must be between 0 and 1.")
        return value
    
# sessioin state schema 
class StepLog(BaseModel):
    """ 
    Represents a single step in the session history
    Will store each step in firestore
    """
    step_number: int
    action: Optional[Action]
    confidence: float
    goal_completed:bool
    timestamp:float
    



        

