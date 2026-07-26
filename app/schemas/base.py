"""Shared Pydantic base models for splanly schemas."""

from pydantic import BaseModel


class ORMModel(BaseModel):
    """Base model for schemas that map from SQLAlchemy ORM objects.
    
    Eliminates the need to repeat `model_config = {"from_attributes": True}` 
    on every Read schema.
    """

    model_config = {"from_attributes": True}
