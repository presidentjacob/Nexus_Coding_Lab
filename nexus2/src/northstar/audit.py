import json
import os
from dataclasses import asdict, dataclass

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


class FileAuditStore:
    """Stores one JSON object per line; each operation opens and closes the file."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = os.fspath(path)

    def record_deactivation(self, customer_id: str, actor_id: str, reason: str) -> None:
        record = DeactivationAuditRecord(customer_id, actor_id, reason.strip())
        with open(self._path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record)) + "\n")

    @property
    def records(self) -> list[DeactivationAuditRecord]:
        try:
            with open(self._path, encoding="utf-8") as handle:
                return [DeactivationAuditRecord(**json.loads(line)) for line in handle if line.strip()]
        except FileNotFoundError:
            return []