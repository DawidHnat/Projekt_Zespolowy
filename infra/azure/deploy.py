#!/usr/bin/env python3
"""Render a cloud-init config and deploy the Fleet-Flow development VM."""

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MEMBERS = {
    "jczaja51": ("Jakub Czaja", "jczaja51"),
    "dawidhnat": ("Dawid Hnat", "DawidHnat"),
    "jnazarewiczs": ("Jakub Nazarewicz", "jnazarewiczs"),
    "mglowacki0": ("Marcel Głowacki", "mglowacki0"),
}


def read_keys(directory):
    keys = {}
    for username in MEMBERS:
        path = directory / f"{username}.pub"
        values = path.read_text().strip().splitlines() if path.exists() else []
        if path.exists():
            if not values or any(not line.startswith(("ssh-ed25519 ", "ssh-rsa ", "ecdsa-sha2-", "sk-ssh-ed25519@", "sk-ecdsa-sha2-")) for line in values):
                raise ValueError(f"{path}: oczekiwany jest klucz PUBLICZNY OpenSSH (.pub).")
            subprocess.run(["ssh-keygen", "-lf", str(path)], check=True, stdout=subprocess.DEVNULL)
        keys[username] = values
    return keys


def cloud_config(keys, admin):
    users = []
    for username, (name, _) in MEMBERS.items():
        privileged = username in {admin, "dawidhnat"}
        user = {
            "name": username,
            "gecos": name,
            "shell": "/bin/bash",
            "lock_passwd": True,
            "groups": ["fleet-flow"] + (["sudo", "docker"] if privileged else []),
            "ssh_authorized_keys": keys[username],
            "sudo": ["ALL=(ALL) NOPASSWD:ALL"] if privileged else None,
        }
        if not keys[username]:
            del user["ssh_authorized_keys"]
        users.append(user)
    ssh = "\n".join([
        "PasswordAuthentication no",
        "KbdInteractiveAuthentication no",
        "PubkeyAuthentication yes",
        "AuthenticationMethods publickey",
        "PermitRootLogin no",
        "X11Forwarding no",
        "MaxAuthTries 3",
        "AllowUsers " + " ".join(MEMBERS),
        "",
    ])
    return {
        "hostname": "fleet-flow-dev",
        "manage_etc_hosts": True,
        "timezone": "Europe/Warsaw",
        "ssh_pwauth": False,
        "disable_root": True,
        "groups": ["fleet-flow", "docker"],
        "users": users,
        "package_update": True,
        "package_upgrade": True,
        "packages": ["git", "python3-venv", "python3-pip", "build-essential", "acl", "jq", "unzip", "docker.io", "docker-compose-v2", "fail2ban", "unattended-upgrades"],
        "write_files": [
            {"path": "/etc/ssh/sshd_config.d/00-fleet-flow.conf", "owner": "root:root", "permissions": "0644", "content": ssh},
            {"path": "/etc/fail2ban/jail.d/fleet-flow.local", "owner": "root:root", "permissions": "0644", "content": "[sshd]\nenabled = true\nbackend = systemd\nmaxretry = 5\nfindtime = 10m\nbantime = 1h\n"},
        ],
        "runcmd": [
            ["install", "-d", "-o", "root", "-g", "fleet-flow", "-m", "2770", "/srv/fleet-flow", "/srv/fleet-flow/apps", "/srv/fleet-flow/backups"],
            ["setfacl", "-m", "g:fleet-flow:rwx,d:u::rwx,d:g::rwx,d:g:fleet-flow:rwx,d:o::---", "/srv/fleet-flow", "/srv/fleet-flow/apps", "/srv/fleet-flow/backups"],
            ["bash", "-c", "if [ ! -e /swapfile ]; then fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile; fi; swapon /swapfile; if ! grep -q '^/swapfile ' /etc/fstab; then echo '/swapfile none swap sw 0 0' >> /etc/fstab; fi"],
            ["systemctl", "enable", "--now", "docker", "fail2ban"],
            ["install", "-d", "-m", "0755", "/run/sshd"],
            ["bash", "-c", "/usr/sbin/sshd -t && systemctl reload-or-restart ssh"],
        ],
        "final_message": "Fleet-Flow dev server: cloud-init finished in $UPTIME seconds.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subscription", required=True, help="ID docelowej subskrypcji Azure for Students")
    parser.add_argument("--resource-group", default="fleet-flow-dev-rg")
    parser.add_argument("--location", default="polandcentral")
    parser.add_argument("--vm-name", default="fleet-flow-dev")
    parser.add_argument("--vm-size", default="Standard_B2als_v2")
    parser.add_argument("--admin", choices=MEMBERS, default="jczaja51")
    parser.add_argument("--keys-dir", type=Path, default=ROOT / "public-keys")
    parser.add_argument("--ssh-source", default="*", help="IP/CIDR uprawniony do SSH; * dla zmiennych adresów zespołu")
    parser.add_argument("--render-only", action="store_true", help="Przygotuj pliki lokalnie bez wywołań Azure")
    parser.add_argument("--validate-only", action="store_true", help="Utwórz pustą grupę zasobów i zweryfikuj szablon, bez tworzenia VM")
    parser.add_argument("--no-power-schedule", action="store_true", help="Pomiń harmonogramy startu i dealokacji")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,39}", args.vm_name):
        parser.error("Nazwa VM musi zawierać 3–40 małych liter, cyfr lub myślników.")
    keys = read_keys(args.keys_dir)
    if len(keys[args.admin]) != 1:
        parser.error(f"Administrator {args.admin} wymaga dokładnie jednego klucza publicznego w {args.keys_dir / (args.admin + '.pub')}.")
    config = cloud_config(keys, args.admin)
    config["hostname"] = args.vm_name
    data = "#cloud-config\n" + json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    values = {
        "location": args.location,
        "vmName": args.vm_name,
        "vmSize": args.vm_size,
        "adminUsername": args.admin,
        "adminPublicKey": keys[args.admin][0],
        "cloudInitBase64": base64.b64encode(data.encode()).decode(),
        "sshSource": args.ssh_source,
    }
    directory = ROOT / ".local"
    directory.mkdir(exist_ok=True, mode=0o700)
    cloud_file = directory / "cloud-init.yaml"
    cloud_file.write_text(data)
    parameters = directory / "parameters.json"
    parameters.write_text(json.dumps({
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {key: {"value": value} for key, value in values.items()},
    }, indent=2) + "\n")
    os.chmod(parameters, 0o600)
    os.chmod(cloud_file, 0o600)
    print(f"Pliki przygotowane: {directory}", flush=True)
    print("Konta bez klucza (logowanie zablokowane): " + ", ".join(user for user in MEMBERS if not keys[user]), flush=True)
    power_command = [sys.executable, str(ROOT / "power_schedule.py"), "--subscription", args.subscription, "--resource-group", args.resource_group, "--vm-name", args.vm_name, "--location", args.location]
    if args.render_only:
        if not args.no_power_schedule:
            subprocess.run(power_command + ["--render-only"], check=True)
        return
    def az_command(arguments):
        return ["az"] + arguments + ["--subscription", args.subscription, "--only-show-errors"]

    subscription = json.loads(subprocess.check_output(az_command(["rest", "--method", "get", "--url", f"https://management.azure.com/subscriptions/{args.subscription}?api-version=2022-12-01", "-o", "json"]), text=True))
    if subscription.get("state") != "Enabled" or not subscription.get("subscriptionPolicies", {}).get("quotaId", "").startswith("AzureForStudents") or subscription.get("subscriptionPolicies", {}).get("spendingLimit") != "On":
        raise ValueError("Wymagana aktywna subskrypcja Azure for Students z włączonym limitem wydatków.")
    subprocess.run(az_command(["group", "create", "--name", args.resource_group, "--location", args.location, "--tags", "project=fleet-flow", "environment=development", "-o", "none"]), check=True)
    command = ["deployment", "group", "validate" if args.validate_only else "create", "--resource-group", args.resource_group, "--name", "fleet-flow-dev", "--mode", "Incremental", "--template-file", str(ROOT / "main.json"), "--parameters", "@" + str(parameters)]
    if not args.validate_only:
        command += ["--query", "properties.outputs", "-o", "json"]
    else:
        command += ["--query", "{error:error,provisioningState:properties.provisioningState}", "-o", "json"]
    subprocess.run(az_command(command), check=True)
    if not args.validate_only and not args.no_power_schedule:
        subprocess.run(power_command, check=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
