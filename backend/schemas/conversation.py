from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Conversation(BaseModel):
    id:int
    user_id:int
    thread_id:str
    title:str
    created_at:datetime
    updated_at:datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )