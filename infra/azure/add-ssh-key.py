#!/usr/bin/env python3
"""Install a team member's PUBLIC SSH key on the existing server."""

import argparse
import base64
from pathlib import Path
import shlex
import subprocess

from deploy import MEMBERS

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("username", choices=MEMBERS)
parser.add_argument("public_key", type=Path)
parser.add_argument("--host", required=True)
parser.add_argument("--admin", default="jczaja51", choices=MEMBERS)
parser.add_argument("--identity", type=Path, required=True)
args = parser.parse_args()
key = args.public_key.read_text().strip()
if "\n" in key or not key.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-", "sk-ssh-ed25519@", "sk-ecdsa-sha2-")):
    parser.error("Podaj pojedynczy klucz PUBLICZNY OpenSSH, nie prywatny.")
subprocess.run(["ssh-keygen", "-lf", str(args.public_key)], check=True)
encoded = base64.b64encode((key + "\n").encode()).decode()
# The choices above constrain the username; key data is base64 and shell-quoted.
script = f"""set -eu
user={shlex.quote(args.username)}
directory=/home/$user/.ssh
key=$(printf '%s' {shlex.quote(encoded)} | base64 --decode)
id "$user" >/dev/null
install -d -m 700 -o "$user" -g "$user" "$directory"
touch "$directory/authorized_keys"
grep -qFx -- "$key" "$directory/authorized_keys" || printf '%s\\n' "$key" >> "$directory/authorized_keys"
chown "$user:$user" "$directory/authorized_keys"
chmod 600 "$directory/authorized_keys"
echo "Publiczny klucz dodany dla $user. Właściciel musi sprawdzić logowanie ze swojego komputera."
"""
subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-i", str(args.identity.expanduser()), f"{args.admin}@{args.host}", "sudo", "bash", "-s"], input=script, text=True, check=True)
destination = Path(__file__).resolve().parent / "public-keys" / f"{args.username}.pub"
destination.parent.mkdir(exist_ok=True)
existing = destination.read_text().strip().splitlines() if destination.exists() else []
if key not in existing:
    existing.append(key)
destination.write_text("\n".join(existing) + "\n")
print(f"Klucz publiczny zapisany do kolejnego wdrożenia: {destination}")
