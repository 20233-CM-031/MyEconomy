"""Identity, household and consent API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)

from myeconomy.domain.consent import ConsentPurpose, DataCategory, RecipientType

DisplayName = Annotated[str, Field(min_length=1, max_length=80)]
HouseholdName = Annotated[str, Field(min_length=1, max_length=100)]
RecipientId = Annotated[str, Field(min_length=1, max_length=128)]
TermsVersion = Annotated[str, Field(min_length=1, max_length=32)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=128)
    display_name: DisplayName

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name must not be empty.")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_password_content(cls, value: SecretStr) -> SecretStr:
        password = value.get_secret_value()
        if password.isspace():
            raise ValueError("Password must contain non-whitespace characters.")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    email_verified: bool
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: AwareDatetime
    user: UserResponse


class HouseholdCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: HouseholdName

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Household name must not be empty.")
        return normalized


class HouseholdInvitationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class HouseholdInvitationResponse(BaseModel):
    id: UUID
    household_id: UUID
    invited_email: EmailStr
    invitation_token: str
    expires_at: AwareDatetime
    delivery_status: str = "manual_share_required"


class HouseholdInvitationAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invitation_token: Annotated[str, Field(min_length=32, max_length=128)]


class HouseholdInvitationRevokedResponse(BaseModel):
    id: UUID
    status: str
    revoked_at: AwareDatetime | None


class HouseholdResponse(BaseModel):
    id: UUID
    name: str
    role: str
    created_at: datetime


class HouseholdMemberResponse(BaseModel):
    user_id: UUID
    display_name: str
    role: str
    joined_at: datetime


class ConsentGrantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purpose: ConsentPurpose
    data_categories: list[DataCategory] = Field(min_length=1, max_length=10)
    recipient_type: RecipientType
    recipient_id: RecipientId
    terms_version: TermsVersion
    confirmed: Literal[True]
    expires_at: AwareDatetime | None = None

    @field_validator("recipient_id", "terms_version")
    @classmethod
    def strip_bounded_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be empty.")
        return normalized

    @model_validator(mode="after")
    def reject_duplicate_categories(self) -> ConsentGrantRequest:
        if len(self.data_categories) != len(set(self.data_categories)):
            raise ValueError("data_categories must not contain duplicates.")
        return self


class ConsentGrantResponse(BaseModel):
    id: UUID
    purpose: str
    data_categories: list[str]
    recipient_type: str
    recipient_id: str
    terms_version: str
    status: str
    granted_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class ConsentCheckResponse(BaseModel):
    allowed: bool
    purpose: ConsentPurpose
    category: DataCategory
    recipient_type: RecipientType
    recipient_id: str
    note: str = (
        "This is an informational check; data access must enforce consent "
        "in its own service transaction."
    )


class ConsentTermsResponse(BaseModel):
    purpose: ConsentPurpose
    version: str
    title: str
    summary: str
    allowed_categories: list[DataCategory]
    recipient_type: RecipientType
    default_expiry_days: int = 90
    maximum_expiry_days: int = 365
    revocation_note: str


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: Annotated[str, Field(min_length=32, max_length=128)]


class EmailVerificationResponse(BaseModel):
    email_verified: Literal[True]
    message: str = "Email address verified."
