import uuid
from src.models import PanelReview
from src.services.runs import require_completed
from src.utils.time import now
from src.utils.serialization import serialize
def create(db,payload,user):
 require_completed(db,payload.run_id)
 item=PanelReview(id=str(uuid.uuid4()),created_at=now(),author=user["email"],**payload.model_dump());db.add(item);db.commit();return serialize(item)
