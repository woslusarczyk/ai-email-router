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

DEPARTMENT_EMAILS: dict[Department, str] = {
    Department.HUMAN_RESOURCES: "human-resources@example.com",
    Department.HELP_DESK: "help-desk@example.com",
    Department.IT: "it@example.com",
    Department.KADRY: "kadry@example.com",
    Department.OTHER: "other@example.com",
}
