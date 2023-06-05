def username_from_email(email: str):
    return '@' + email.split('@')[0]


