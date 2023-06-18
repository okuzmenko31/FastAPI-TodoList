"""
The idea of token is taken from my another project.

Link: https://github.com/okuzmenko31/drf-ecommerce/blob/main/ecommerce/apps/users/token.py
"""
import binascii
import os
from src import config
from sqlalchemy import select, exists, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AuthToken
from typing import NamedTuple, Optional
from jinja2 import Environment, select_autoescape, PackageLoader
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

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


env = Environment(
    loader=PackageLoader('src', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class SendEmailMixin:
    def __init__(self, email: str, url: str):
        self.email = email
        self.url = url

    async def maker_send_mail(self, subject, template):
        # Define the config
        conf = ConnectionConfig(
            MAIL_USERNAME=config.SMTP_USERNAME,
            MAIL_PASSWORD=config.SMTP_PASSWORD,
            MAIL_FROM=config.SMTP_USER,
            MAIL_PORT=config.SMTP_PORT,
            MAIL_SERVER=config.SMTP_HOST,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        # Generate the HTML template based on the template name
        template = env.get_template(f'{template}.html')

        html = template.render(
            username=self.email,
            url=self.url,
            subject=subject
        )

        # Define the message options
        message = MessageSchema(
            subject=subject,
            recipients=[self.email],
            body=html,
            subtype="html"
        )

        # Send the email
        fm = FastMail(conf)
        await fm.send_message(message)

    async def send_mail(self, subject):
        await self.maker_send_mail(subject, 'verification')


class AuthTokenQueryMixin:
    """
    Mixin which is responsible for returning
    query for token instance.
    """
    query = None
    __statement = None

    async def query_by_token_email(self,
                                   statement,
                                   email: Optional[str] = None,
                                   token: Optional[str] = None,
                                   token_type: Optional[str] = None):
        stmt = statement
        if email is not None and token is None:
            self.query = stmt.filter_by(token_owner=email, token_type=token_type)
        elif token is not None and email is None:
            self.query = stmt.filter_by(token=token)
        elif email is not None and token is not None:
            self.query = stmt.filter_by(token=token, token_owner=email)
        return self.query

    @property
    async def select_stmt(self):
        return select(AuthToken)

    @property
    async def delete_stmt(self):
        return delete(AuthToken)


class AuthTokenManager(AuthTokenQueryMixin,
                       MailContextMixin):
    """
    Mixin for creating and sending tokenized email.

    This mixin provides methods for creating and sending tokens via email for
    various token types. Available token types are:
        - SignUp ['su']
        - Change email ['ce']
        - Password reset ['pr']

    Attributes:
        token_type (str): the token type to create.
        mail_with_celery (bool): setting which can help you to send emails with celery.
    """
    token_type = None
    mail_with_celery = False

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_token_exists(self,
                                 email: Optional[str] = None,
                                 token: Optional[str] = None) -> bool:
        """
        Checks the token instance by provided
        token value or email of token owner.
        You can specify them together. Return
        True if token exists or not in another case.

        Args:
            email (str): email of token owner.
            token (str): string token value.
        Returns:
            True or False.
        """
        query = await self.query_by_token_email(
            statement=await self.select_stmt,
            email=email,
            token=token,
            token_type=self.token_type
        )
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
        """
        Creates token instance by provided
        email of token owner. Returns created
        instance of token.

        Args:
            email (str): email of token owner.

        Returns:
            Created token instance.
        """
        token_value = await self.generate_unique_token()
        new_token = AuthToken(
            token=token_value,
            token_type=self.token_type,
            token_owner=email
        )
        self.session.add(new_token)
        await self.session.flush()
        return new_token

    async def delete_exists_token(self,
                                  email: Optional[str] = None,
                                  token: Optional[str] = None):
        """
        Deletes the token instance by provided
        token value or email of token owner.
        You can specify them together.

        Args:
            email (str): email of token owner.
            token (str): string token value.
        """
        query = await self.query_by_token_email(
            statement=await self.delete_stmt,
            email=email,
            token=token,
            token_type=self.token_type
        )
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
                await self.delete_exists_token(email=email)
                token = await self.token_create(email)
            except (Exception,):
                return TokenData(error=MESSAGES['token_miss_error'])
        return TokenData(token=token)

    async def send_tokenized_mail(self, email: str) -> str:
        """
        Method that calls the `_create_token` method to generate
        a token for the given email address, creates a context
        for an email and sends it to the user's email address.
        Returns a success message upon successful email delivery
        or an error message if an error occurs.

        Args:
            email (str): The email address to which the token email will be sent
        Returns:
            A success message upon successful email delivery
            or an error message if an error occurs.
        """
        mail_context = await self.get_context(token_type=self.token_type)
        token_data = await self._create_token(email)

        if token_data.error:
            return token_data.error

        subject = mail_context['subject']
        url = 'http' + '://127.0.0.1:8000' + f'/confirm_email_reg/{token_data.token.token}/{email}'
        mail_mixin = SendEmailMixin(email=email,
                                    url=url)
        if self.mail_with_celery:
            pass
        else:
            await mail_mixin.send_mail(subject)
        return mail_context['success_message']


async def get_token_by_params(token_value: str, token_owner: str, session: AsyncSession):
    """
    Returns token instance by provided token_value,
    toke_owner and session.

    Args:
        token_value (str): string value of the token.
        token_owner (str): email address of token owner.
        session (AsyncSession): AsyncSession instance.
    Returns:
        Token instance or None.
    """
    query = select(AuthToken).filter_by(token=token_value, token_owner=token_owner)
    result = await session.execute(query)
    token_row = result.fetchone()
    if token_row is not None:
        token = token_row[0]
        return token


async def get_token_data(token: str, email: str, session: AsyncSession) -> TokenData:
    """
    Function for getting token data.

    Args:
        token (str): The token string to retrieve.
        email (str): The email of the token owner.
        session (AsyncSession): session object.

    Returns:
        The TokenData object with either the token or an error message.

    Raises:
        Token.DoesNotExist: If the token does not exist.
    """
    token_manager = AuthTokenManager(session=session)
    exist = await token_manager.check_token_exists(email, token)
    if not exist:
        return TokenData(error=MESSAGES['token_miss_error'])
    token = await get_token_by_params(token_value=token, token_owner=email, session=session)
    if token.expired:
        return TokenData(error=MESSAGES['token_expired_error'])
    await token_manager.delete_exists_token(token=token.token)
    return TokenData(token=token)
