import logging
from datetime import datetime
import json

class AuditLogger:
    """
    Layer 4: Audit Trails [cite: 1024]
    """
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("AuditLogger")

    def log_event(self, actor: str, action: str, resource: str, status: str, details: dict = None):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "actor": actor,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {}
        }
        self.logger.info(json.dumps(event))
