"""Lab wiring, not upstream Nexus code. Adapt this to your design.
Do not manufacture audit records in this adapter: production code must write them.
"""
from types import SimpleNamespace
from dataclasses import asdict
from northstar.audit import InMemoryAuditStore
from northstar.auth import AuthorizationService
from northstar.events import EventBus
from northstar.models import Customer
from northstar.notifications import NotificationClient, CustomerNotificationSubscriber
from northstar.repository import InMemoryCustomerRepository
from northstar.services import CustomerLifecycleService


def build():
    repository = InMemoryCustomerRepository()
    repository.save(Customer("c1", "Case Customer", "case@example.com"))
    bus = EventBus()
    client = NotificationClient()
    bus.subscribe(CustomerNotificationSubscriber(client))
    audit = InMemoryAuditStore()
    lifecycle = CustomerLifecycleService(repository, AuthorizationService(), bus, audit)
    return SimpleNamespace(repository=repository, bus=bus, client=client,
                           lifecycle=lifecycle, audit=audit)


def audit_records(system):
    # Return a list of mappings with customer_id, actor_id, reason.
    # Map your real audit objects here if necessary. Never synthesize the answer.
    return [asdict(record) for record in system.audit.records]
