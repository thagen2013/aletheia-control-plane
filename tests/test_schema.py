"""Tests for schema.py — DeploymentRecord and friends."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from aletheia_control_plane.schema import (
    Cadence,
    DeploymentRecord,
    Jurisdiction,
    Phase,
    PrimaryContact,
    RetainerTier,
    TrustDomain,
    is_template_engagement_code,
)
from tests.conftest import make_valid_record_dict


# --- happy path -------------------------------------------------------


def test_valid_record_parses():
    record = DeploymentRecord.model_validate(make_valid_record_dict())
    assert record.engagement_code == "test_engagement_2026"
    assert record.client_legal_name == "Test Client Inc."
    assert record.system_id == "SYS-TEST-001"
    assert record.jurisdictions == [Jurisdiction.FDA]
    assert TrustDomain.AUDIT_TRAIL in record.trust_domains
    assert record.cadence is Cadence.QUARTERLY
    assert record.phase is Phase.ACTIVE
    assert record.retainer_tier is RetainerTier.STANDARD


def test_v_prefix_version_accepted():
    record = DeploymentRecord.model_validate(
        make_valid_record_dict(methodology_version="v0.5.0", hetarios_version="v0.5.0")
    )
    assert record.methodology_version == "v0.5.0"


def test_overlay_id_optional():
    record = DeploymentRecord.model_validate(make_valid_record_dict(overlay_id=None))
    assert record.overlay_id is None


def test_overlay_id_string():
    record = DeploymentRecord.model_validate(
        make_valid_record_dict(overlay_id="overlay-001-test")
    )
    assert record.overlay_id == "overlay-001-test"


@pytest.mark.parametrize(
    "bad_overlay_id",
    [
        "definitely_not_an_overlay",   # no overlay- prefix
        "overlay-",                    # missing digits and trailing token
        "overlay-001",                 # missing trailing token
        "overlay-001-",                # empty trailing token
        "overlay-abc-foo",             # non-digit middle token
        "overlay-001-FOO",             # uppercase trailing token
        "overlay-001-foo bar",         # whitespace in trailing token
        "overlay-001-<short-name>",    # template placeholder syntax
    ],
)
def test_overlay_id_invalid_pattern_rejected(bad_overlay_id):
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(overlay_id=bad_overlay_id)
        )


# --- engagement_code validation ----------------------------------------


@pytest.mark.parametrize(
    "bad_code",
    [
        "",
        "ab",
        "Bad-Hyphen",
        "Has Spaces",
        "UPPERCASE",
        "123_starts_with_digit",
        "_starts_with_underscore",
        "has-hyphen",
    ],
)
def test_invalid_engagement_codes_rejected(bad_code):
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                engagement_code=bad_code,
                workspace_path=f"engagement_workspaces/{bad_code}/",
            )
        )


def test_engagement_code_too_long():
    long_code = "a" + "b" * 100  # 101 chars
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                engagement_code=long_code,
                workspace_path=f"engagement_workspaces/{long_code}/",
            )
        )


# --- system_id validation ----------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "not-uppercase",
        "SYS-LOWER-case",
        "SYS-",
        "SYS-X",  # only one token after SYS
        "WRONG-PREFIX-X",
    ],
)
def test_invalid_system_ids_rejected(bad_id):
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(make_valid_record_dict(system_id=bad_id))


def test_system_id_with_three_tokens_accepted():
    record = DeploymentRecord.model_validate(
        make_valid_record_dict(system_id="SYS-CLIENT-PRODUCT-001")
    )
    assert record.system_id == "SYS-CLIENT-PRODUCT-001"


# --- version validation ------------------------------------------------


@pytest.mark.parametrize(
    "bad_version",
    [
        "",
        "0.5",
        "0.5.0.1",
        "v",
        "0.5.0-",
        "abc",
    ],
)
def test_invalid_versions_rejected(bad_version):
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(methodology_version=bad_version)
        )


def test_prerelease_version_accepted():
    record = DeploymentRecord.model_validate(
        make_valid_record_dict(methodology_version="0.5.0-rc1")
    )
    assert record.methodology_version == "0.5.0-rc1"


# --- enum validation ---------------------------------------------------


def test_unknown_jurisdiction_rejected():
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(jurisdictions=["EU"])
        )


def test_unknown_trust_domain_rejected():
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(trust_domains=["clinical_validation"])
        )


def test_empty_jurisdictions_rejected():
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(make_valid_record_dict(jurisdictions=[]))


def test_empty_trust_domains_rejected():
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(make_valid_record_dict(trust_domains=[]))


def test_duplicate_jurisdictions_rejected():
    with pytest.raises(ValidationError) as exc:
        DeploymentRecord.model_validate(
            make_valid_record_dict(jurisdictions=["FDA", "FDA"])
        )
    assert "duplicate" in str(exc.value)


def test_duplicate_trust_domains_rejected():
    with pytest.raises(ValidationError):
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                trust_domains=["audit_trail", "audit_trail"]
            )
        )


# --- cross-field validation --------------------------------------------


def test_workspace_path_must_match_engagement_code():
    with pytest.raises(ValidationError) as exc:
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                engagement_code="abc_2026",
                workspace_path="engagement_workspaces/wrong_code/",
            )
        )
    assert "workspace_path" in str(exc.value)


def test_interaction_before_deployment_rejected():
    with pytest.raises(ValidationError) as exc:
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                deployment_date=date(2026, 5, 1),
                last_interaction_date=date(2026, 1, 1),
            )
        )
    assert "last_interaction_date" in str(exc.value)


def test_self_test_before_deployment_rejected():
    with pytest.raises(ValidationError) as exc:
        DeploymentRecord.model_validate(
            make_valid_record_dict(
                deployment_date=date(2026, 5, 1),
                last_self_test_verified=date(2026, 1, 1),
                last_interaction_date=date(2026, 5, 5),
            )
        )
    assert "last_self_test_verified" in str(exc.value)


def test_optional_dates_can_be_none():
    record = DeploymentRecord.model_validate(
        make_valid_record_dict(
            last_interaction_date=None,
            last_self_test_verified=None,
        )
    )
    assert record.last_interaction_date is None
    assert record.last_self_test_verified is None


# --- email validation --------------------------------------------------


def test_valid_email_accepted():
    contact = PrimaryContact(
        name="X", role="Y", email="someone@example.com"
    )
    assert contact.email == "someone@example.com"


@pytest.mark.parametrize(
    "bad_email",
    [
        "",
        "not-an-email",
        "missing-at.com",
        "@no-local.com",
        "no-domain@",
        "no-tld@example",
        "two@@example.com",
    ],
)
def test_invalid_email_rejected(bad_email):
    with pytest.raises(ValidationError):
        PrimaryContact(name="X", role="Y", email=bad_email)


def test_empty_contact_name_rejected():
    with pytest.raises(ValidationError):
        PrimaryContact(name="", role="Y", email="a@b.com")


def test_empty_contact_role_rejected():
    with pytest.raises(ValidationError):
        PrimaryContact(name="X", role="", email="a@b.com")


# --- template detection ------------------------------------------------


def test_is_template_engagement_code():
    assert is_template_engagement_code("") is True
    assert is_template_engagement_code("<engagement_code>") is True
    assert is_template_engagement_code("real_code_2026") is False
    assert is_template_engagement_code("anything") is False
