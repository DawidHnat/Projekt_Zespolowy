"""Local account administration. Passwords are prompted, never CLI arguments."""

import argparse
import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import delete

from app.core.database import make_engine, make_sessions
from app.core.settings import Settings
from app.modules.auth.models import PasswordReset, User
from app.modules.auth.service import find_user, password_hasher, revoke_sessions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["create-user", "set-password", "set-email"])
    parser.add_argument("username")
    parser.add_argument("--name")
    parser.add_argument("--role", choices=["admin", "editor", "viewer"], default="viewer")
    parser.add_argument("--email")
    args = parser.parse_args()
    email = None
    if args.email:
        try:
            email = TypeAdapter(EmailStr).validate_python(args.email)
        except ValidationError:
            parser.error("Podaj poprawny adres e-mail właściciela konta")
    if args.operation == "set-email" and not email:
        parser.error("Operacja wymaga --email")
    password = None
    if args.operation != "set-email":
        password = getpass.getpass("Hasło (minimum 12 znaków): ")
        if len(password) < 12 or password != getpass.getpass("Powtórz hasło: "):
            parser.error("Hasła muszą być zgodne i mieć przynajmniej 12 znaków")
    engine = make_engine(Settings.from_environment())
    try:
        with make_sessions(engine)() as session:
            user = find_user(session, args.username)
            if args.operation == "create-user":
                if user:
                    parser.error("Konto już istnieje")
                user = User(
                    username=args.username.strip().lower(),
                    display_name=args.name or args.username,
                    role=args.role,
                    password_hash=password_hasher.hash(password),
                    email=email,
                )
                session.add(user)
            else:
                if not user:
                    parser.error("Konto nie istnieje")
                if args.operation == "set-email":
                    user.email = email
                else:
                    user.password_hash = password_hasher.hash(password)
                    revoke_sessions(session, user)
                session.execute(delete(PasswordReset).where(PasswordReset.user_id == user.id))
            session.commit()
    finally:
        engine.dispose()
    print("Konto zapisane; hasło nie zostało wypisane")


if __name__ == "__main__":
    main()
