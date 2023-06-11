import re
from typing import NamedTuple, Optional


class PasswordValidationData(NamedTuple):
    error: Optional[str] = None
    success: Optional[bool] = None


def validate_password(password: str) -> PasswordValidationData:
    if not re.search("[a-z]", password):
        return PasswordValidationData(error='Password must contain letters a-z!')
    if not re.search("[0-9]", password):
        return PasswordValidationData(error='Password must contain number 0-9!')
    if not re.search("[A-Z]", password):
        return PasswordValidationData(error='Password must contain letters A-Z!')
    if len(password) < 9:
        return PasswordValidationData(error='Password length must be more than 9 symbols!')
    return PasswordValidationData(success=True)
