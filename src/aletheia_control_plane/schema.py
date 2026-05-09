"""Schema for deployment records.

The deployment record schema is defined here as a pydantic model. The
canonical YAML lives in ``deployments/_template_deployment.yaml``;
this module is the machine-readable counterpart used by the validator,
scaffolder, and reporting commands.

Schema version is tracked via ``SCHEMA_VERSION``; if the schema
evolves, bump this and add migration logic in
``aletheia_control_plane.migration`` (not yet present).
"""

from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


SCHEMA_VERSION = "0.1.0"


# --- enums --------------------------------------------------------------


class Jurisdiction(str, Enum):
    FDA = "FDA"
    NMPA = "NMPA"
    CE = "CE"
    PMDA = "PMDA"
    MFDS = "MFDS"
    OTHER = "other"


class TrustDomain(str, Enum):
    AUDIT_TRAIL = "audit_trail"
    MODEL_VALIDATION = "model_validation"
    DATA_QUALITY = "data_quality"


class Cadence(str, Enum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class Phase(str, Enum):
    DISCOVERY = "discovery"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    TRANSITIONING = "transitioning"
    CLOSED = "closed"


class RetainerTier(str, Enum):
    NONE = "none"
    FOUNDATION = "foundation"
    STANDARD = "standard"
    EXTENDED = "extended"


# --- field constraints --------------------------------------------------


# Engagement code: lowercase letters, digits, underscores. Must start
# with a letter. No hyphens, no spaces, no uppercase.
ENGAGEMENT_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]+$")

EngagementCode = Annotated[
    str,
    StringConstraints(min_length=3, max_length=64, pattern=r"^[a-z][a-z0-9_]+$"),
]

# Semantic version, e.g. "0.5.0". Allow optional pre-release suffix.
SemverString = Annotated[
    str,
    StringConstraints(pattern=r"^v?\d+\.\d+\.\d+(-[a-z0-9.]+)?$"),
]

# System ID: SYS-<TOKEN>-<TOKEN> form, uppercase tokens.
SystemId = Annotated[
    str,
    StringConstraints(pattern=r"^SYS-[A-Z0-9]+(-[A-Z0-9]+)+$"),
]


# --- nested models ------------------------------------------------------


class PrimaryContact(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    email: Annotated[
        str,
        StringConstraints(
            min_length=3,
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        ),
    ]


# --- main model ---------------------------------------------------------


class DeploymentRecord(BaseModel):
    """A single Hetarios deployment under consultant management."""

    engagement_code: EngagementCode
    client_legal_name: str = Field(..., min_length=1)
    system_id: SystemId
    system_name: str = Field(..., min_length=1)
    deployment_date: date
    hetarios_version: SemverString
    methodology_version: SemverString
    jurisdictions: list[Jurisdiction] = Field(..., min_length=1)
    trust_domains: list[TrustDomain] = Field(..., min_length=1)
    overlay_id: str | None = None
    last_self_test_verified: date | None = None
    last_interaction_date: date | None = None
    cadence: Cadence = Cadence.QUARTERLY
    phase: Phase = Phase.ONBOARDING
    retainer_tier: RetainerTier = RetainerTier.NONE
    notes: str = ""
    primary_contact: PrimaryContact
    workspace_path: str

    @field_validator("jurisdictions", "trust_domains")
    @classmethod
    def _no_duplicates(cls, value: list) -> list:
        if len(value) != len(set(value)):
            raise ValueError("duplicate values not allowed")
        return value

    @model_validator(mode="after")
    def _workspace_path_matches_engagement_code(self) -> DeploymentRecord:
        expected = f"engagement_workspaces/{self.engagement_code}/"
        if self.workspace_path != expected:
            raise ValueError(
                f"workspace_path {self.workspace_path!r} does not match "
                f"engagement_code {self.engagement_code!r} "
                f"(expected {expected!r})"
            )
        return self

    @model_validator(mode="after")
    def _interaction_after_deployment(self) -> DeploymentRecord:
        if (
            self.last_interaction_date is not None
            and self.last_interaction_date < self.deployment_date
        ):
            raise ValueError(
                "last_interaction_date is earlier than deployment_date"
            )
        return self

    @model_validator(mode="after")
    def _self_test_after_deployment(self) -> DeploymentRecord:
        if (
            self.last_self_test_verified is not None
            and self.last_self_test_verified < self.deployment_date
        ):
            raise ValueError(
                "last_self_test_verified is earlier than deployment_date"
            )
        return self


def is_template_engagement_code(code: str) -> bool:
    """Return True if ``code`` is the template placeholder.

    Template files use the empty string or ``"<engagement_code>"`` as a
    placeholder. These are not valid engagement codes; they exist so
    that the template files are valid YAML.
    """

    return code in {"", "<engagement_code>"}
