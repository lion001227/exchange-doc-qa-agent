from typing import Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    id:int
    user_id:int
    conversation_id:int
    role:str
    content:Optional[str]=None
    # metadata:Optional[Dict[str,Any]]=Field(None,alias="meta_data")
    input_token_usage:Optional[int]=None
    output_token_usage:Optional[int]=None
    total_token_usage:Optional[int]=None
    latency:Optional[float]=None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )