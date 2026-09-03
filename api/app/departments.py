from enum import Enum


class Department(str, Enum):
    HUMAN_RESOURCES = "human-resources"
    HELP_DESK = "help-desk"
    IT = "it"
    KADRY = "kadry"
    OTHER = "other"

    @property
    def email(self) -> str:
        return f"{self.value}@example.com"
