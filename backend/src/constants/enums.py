from enum import Enum
class Role(str,Enum):
 admin="admin"
 analyst="analyst"
 viewer="viewer"
class RunStatus(str,Enum):
 queued="queued"
 running="running"
 completed="completed"
 failed="failed"
class Decision(str,Enum):
 accepted="accepted"
 needs_attention="needs_attention"
