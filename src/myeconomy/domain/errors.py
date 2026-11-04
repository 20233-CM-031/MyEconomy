"""Stable application errors shared by domain and application layers."""


class ApplicationError(Exception):
    """Base error carrying a safe public code and HTTP status."""

    code = "application_error"
    status_code = 400
    public_message = "The request could not be completed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        self.message = message or self.public_message


class ConflictError(ApplicationError):
    code = "conflict"
    status_code = 409
    public_message = "The requested resource conflicts with existing state."


class AuthenticationError(ApplicationError):
    code = "authentication_required"
    status_code = 401
    public_message = "Authentication is required or the session is no longer valid."


class NotFoundError(ApplicationError):
    code = "not_found"
    status_code = 404
    public_message = "The requested resource was not found."


class AuthorizationError(ApplicationError):
    code = "forbidden"
    status_code = 403
    public_message = "You are not authorized to perform this action."


class ConsentScopeError(ApplicationError):
    code = "invalid_consent_scope"
    status_code = 422
    public_message = "The requested consent scope is not permitted."


class ConsentRequiredError(ApplicationError):
    code = "consent_required"
    status_code = 403
    public_message = "An active consent grant is required for this operation."


class VerificationError(ApplicationError):
    code = "invalid_verification_token"
    status_code = 400
    public_message = "The verification token is invalid, expired or already used."


class RateLimitError(ApplicationError):
    code = "rate_limited"
    status_code = 429
    public_message = "Too many requests. Please wait before trying again."


class ServiceUnavailableError(ApplicationError):
    code = "service_unavailable"
    status_code = 503
    public_message = "A required delivery service is temporarily unavailable."


class FinancialDataValidationError(ApplicationError):
    code = "financial_data_invalid"
    status_code = 422
    public_message = "The financial data could not be accepted."


class IdempotencyConflictError(ConflictError):
    code = "idempotency_conflict"
    public_message = "This idempotency key was already used with different request content."
