#!/usr/bin/env python3
"""Create ignored local configuration without overwriting existing credentials."""

from pathlib import Path
import os
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / ".env"
    if destination.exists():
        print(".env już istnieje; pozostawiono jego zawartość bez zmian.")
        return
    password = secrets.token_urlsafe(24)
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    content = content.replace("POSTGRES_PASSWORD=\n", f"POSTGRES_PASSWORD={password}\n")
    content = content.replace("YOUR_LOCAL_PASSWORD", password)
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as file:
        file.write(content)
    print("Utworzono lokalny .env z losowym hasłem bazy; sekretów nie wypisano.")
    print("Domyślny tryb: demo. Dane WEBFLEET uzupełnij wyłącznie lokalnie.")


if __name__ == "__main__":
    main()
