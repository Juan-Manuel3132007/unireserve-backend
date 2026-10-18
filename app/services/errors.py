"""Excepciones de dominio. Se traducen a respuestas HTTP en app/main.py."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, detail: str, code: str = "domain_error"):
        self.detail = detail
        self.code = code
        super().__init__(detail)


class NotFoundError(DomainError):
    status_code = 404

    def __init__(self, detail: str = "Recurso no encontrado."):
        super().__init__(detail, code="not_found")


class ConflictError(DomainError):
    status_code = 409

    def __init__(self, detail: str, code: str = "conflict"):
        super().__init__(detail, code=code)


class ForbiddenError(DomainError):
    status_code = 403

    def __init__(self, detail: str = "No tiene permisos para realizar esta accion."):
        super().__init__(detail, code="forbidden")


class ValidationError(DomainError):
    status_code = 422

    def __init__(self, detail: str):
        super().__init__(detail, code="validation_error")
