from fastapi import status, HTTPException


class CinemaException(HTTPException):
    """Base exception for the entire application."""
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(status_code=status_code, detail=detail)


class DuplicatePurchaseException(CinemaException):
    """Thrown if the user attempts to purchase a movie they already own."""
    def __init__(self, detail: str = "You already own this movie"):
        super().__init__(
            detail=detail, status_code=status.HTTP_400_BAD_REQUEST
        )


class PermissionDeniedException(CinemaException):
    """Thrown when access rights are insufficient."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)
