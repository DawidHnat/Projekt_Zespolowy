"""Local account administration. Passwords are prompted, never CLI arguments."""

import argparse
import getpass

from app.core.database import make_engine, make_sessions
from app.core.settings import Settings
from app.modules.auth.models import User
from app.modules.auth.service import find_user, password_hasher, revoke_sessions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["create-user", "set-password"])
    parser.add_argument("username")
    parser.add_argument("--name")
    parser.add_argument("--role", choices=["admin", "editor", "viewer"], default="viewer")
    args = parser.parse_args()
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
                )
                session.add(user)
            else:
                if not user:
                    parser.error("Konto nie istnieje")
                user.password_hash = password_hasher.hash(password)
                revoke_sessions(session, user)
            session.commit()
    finally:
        engine.dispose()
    print("Konto zapisane; hasło nie zostało wypisane")


if __name__ == "__main__":
    main()
