from dataclasses import dataclass

@dataclass(frozen=True)
class DeactivationAuditRecord:
    customer_id: str
    actor_id: str
    reason: str

class InMemoryAuditStore:
    def __init__(self):
        self._records: list[DeactivationAuditRecord] = []

    def record_deactivation(self, customer_id: str, actor_id: str, reason: str) -> None:
        self._records.append(DeactivationAuditRecord(customer_id, actor_id, reason.strip(),))

    @property
    def records(self) -> list[DeactivationAuditRecord]:
        return self._records.copy()