from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmployeeId:
    """Value Object for Employee ID.

    KISS: immutable wrapper around a string with a couple of simple factories.
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("EmployeeId.value must be str")
        if self.value == "":
            raise ValueError("EmployeeId cannot be empty")

    def __str__(self) -> str:  # for CSV/JSON serialization and dict keys
        return self.value

    @classmethod
    def from_raw(cls, s: str) -> "EmployeeId":
        return cls(s)

    @classmethod
    def from_tag_identifier(cls, identifier: bytes) -> "EmployeeId":
        """Create EmployeeId from NFC tag identifier bytes as uppercase hex."""
        if not isinstance(identifier, (bytes, bytearray)):
            raise TypeError("identifier must be bytes-like")
        return cls(bytes(identifier).hex().upper())

    def to_csv(self) -> str:
        return self.value
