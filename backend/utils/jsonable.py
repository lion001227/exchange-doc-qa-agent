from langchain_core.messages import BaseMessage
import json

def to_jsonable(obj):
    return json.loads(json.dumps(obj,
                                 default=lambda o:o.model_dump() if isinstance(o,BaseMessage) else str(o),))