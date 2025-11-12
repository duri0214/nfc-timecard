from .service import WorkRecord, compute_hours, is_acceptable_card
from .valueobject import EmployeeId

__all__ = [
    "WorkRecord",
    "compute_hours",
    "is_acceptable_card",
    "EmployeeId",
    "make_employee_id_from_tag_identifier",
]


def make_employee_id_from_tag_identifier(identifier: bytes) -> str:
    """Compatibility helper: create EmployeeId from tag bytes and return str.

    Existing code expects a plain string employee_id; internally we now have
    a Value Object, but we keep this simple bridge for callers.
    """
    return str(EmployeeId.from_tag_identifier(identifier))
