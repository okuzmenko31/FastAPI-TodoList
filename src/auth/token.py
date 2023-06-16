"""
This idea of token is taken from my another project.

Link: https://github.com/okuzmenko31/drf-ecommerce/blob/main/ecommerce/apps/users/token.py
"""
import binascii
import os
from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AuthToken
from typing import NamedTuple, Optional

MESSAGES = {
    'token_miss_error': ('This token does not exist or belongs '
                         'to another user!'),
    'token_expired_error': 'Signature expired',
    'no_user': 'No such user with this email address!',
    'complete_registration': 'CodeSphere - complete registration.',
    'complete_email_changing': 'CodeSphere - complete changing email',
    'complete_password_reset': 'CodeSphere - complete password reset',
    'registration_mail_sent': ('Mail with registration link has '
                               'been sent to your email.'),
    'email_changing_sent': ('Mail with email changing confirmation '
                            'has been sent to your new email. '
                            'Your email in this account will be '
                            'changed after confirmation.'),

    'password_reset_sent': ('Mail with password reset confirmation has been sent '
                            'to your email.')
}


class TokenData(NamedTuple):
    token: Optional[AuthToken] = None
    email: Optional[str] = None
    token_type: Optional[str] = None
    error: Optional[str] = None


class TokenTypes:
    SIGNUP = 'su'
    CHANGE_EMAIL = 'ce'
    PASSWORD_RESET = 'pr'


class MailContextMixin:
    """
    Mixin which creates context for mail and
    returns success message the content of which
    will depend on the type of token.
    """
    __subject = None
    __message = ''
    __success_message = None

    @classmethod
    async def _set_subject(cls, token_type):
        if token_type == 'su':
            cls.__subject = MESSAGES['complete_registration']
        elif token_type == 'ce':
            cls.__subject = MESSAGES['complete_email_changing']
        else:
            cls.__subject = MESSAGES['complete_password_reset']

    @classmethod
    async def _set_success_message(cls, token_type):
        if token_type == 'su':
            cls.__success_message = MESSAGES['registration_mail_sent']
        elif token_type == 'ce':
            cls.__success_message = MESSAGES['email_changing_sent']
        else:
            cls.__success_message = MESSAGES['password_reset_sent']

    async def get_context(self, token_type):
        """
        Returns context with mail subject, message and
        success message for user that mail has been sent.
        """
        await self._set_subject(token_type)
        await self._set_success_message(token_type)

        context = {
            'subject': self.__subject,
            'message': self.__message,
            'success_message': self.__success_message
        }
        return context


class AuthTokenManager(MailContextMixin):
    """
    Mixin for creating and sending tokenized email.

    This mixin provides methods for creating and sending tokens via email for
    various token types. Available token types are:
        - SignUp ['su']
        - Change email ['ce']
        - Password reset ['pr']

    Attributes:
        token_type (str): The token type to create.
        html_message_template (str): The path to the HTML message template.
    """
    token_type = None
    html_message_template = None
    mail_with_celery = False

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_token_exists(self,
                                 email: Optional[str] = None,
                                 token: Optional[str] = None) -> bool:
        query = None
        if email is not None and token is None:
            query = select(AuthToken).filter_by(token_owner=email, token_type=self.token_type)
        elif token is not None and email is None:
            query = select(AuthToken).filter_by(token=token)
        elif email is not None and token is not None:
            query = select(AuthToken).filter_by(token=token, token_owner=email)
        exists_query = exists(query).select()
        result = await self.session.execute(exists_query)
        exists_row = result.fetchone()
        return exists_row[0]

    @staticmethod
    async def __generate_token():
        return binascii.hexlify(os.urandom(16)).decode()

    async def generate_unique_token(self):
        token = await self.__generate_token()
        while await self.check_token_exists(token):
            token = await self.__generate_token()
        return token

    async def token_create(self, email: str) -> AuthToken:
        token_value = await self.generate_unique_token()
        new_token = AuthToken(
            token=token_value,
            token_type=self.token_type,
            token_owner=email
        )
        self.session.add(new_token)
        await self.session.flush()
        return new_token

    async def delete_exists_token(self, email: str) -> None:
        query = delete(AuthToken).filter_by(token_owner=email,
                                            token_type=self.token_type)
        await self.session.execute(query)

    async def _create_token(self, email: str) -> TokenData:
        """
        Method which creates a new token for the given email.

        Args:
            email (str): The email address to associate with the token.

        Returns:
            TokenData: The TokenData object with either the token or an error message.
        """
        token_exists = await self.check_token_exists(email)
        if not token_exists:
            token = await self.token_create(email)
        else:
            try:
                await self.delete_exists_token(email)
                token = self.token_create(email)
            except (Exception,):
                return TokenData(error=MESSAGES['token_miss_error'])
        return TokenData(token=token)
