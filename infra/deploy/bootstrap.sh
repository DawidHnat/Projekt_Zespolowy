#!/usr/bin/env bash
set -euo pipefail
umask 077

[[ $EUID -eq 0 && $# -eq 1 ]] || {
  printf 'Użycie: sudo bash bootstrap.sh /ścieżka/do/klucza-CI.pub\n' >&2
  exit 1
}
for dependency in docker python3 curl ssh-keygen visudo; do
  command -v "$dependency" >/dev/null
done
docker compose version >/dev/null
python3 -c 'import tarfile; assert hasattr(tarfile, "data_filter")'
key_file=$(realpath -- "$1")
awk 'NF { n++; if ($1 != "ssh-ed25519") bad=1 } END { exit (n != 1 || bad) }' "$key_file"
ssh-keygen -lf "$key_file"
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if id fleetdeploy >/dev/null 2>&1; then
  [[ $(id -u fleetdeploy) -ge 1000 ]]
  [[ $(getent passwd fleetdeploy | cut -d: -f6) == /home/fleetdeploy ]]
else
  useradd --create-home --user-group --shell /bin/bash fleetdeploy
fi
passwd -l fleetdeploy >/dev/null
install -d -m 755 -o root -g root /opt/fleet-flow
install -m 755 -o root -g root "$scripts/deploy.sh" /usr/local/sbin/fleet-flow-deploy
install -m 755 -o root -g root "$scripts/receive.sh" /usr/local/bin/fleet-flow-receive
install -d -m 700 -o fleetdeploy -g fleetdeploy /home/fleetdeploy/.ssh
authorized=/home/fleetdeploy/.ssh/authorized_keys
touch "$authorized"
key_line="restrict,command=\"/usr/local/bin/fleet-flow-receive\" $(awk 'NF {print; exit}' "$key_file")"
grep -qxF -- "$key_line" "$authorized" || printf '\n%s\n' "$key_line" >> "$authorized"
chown fleetdeploy:fleetdeploy "$authorized"
chmod 600 "$authorized"
sudoers=$(mktemp)
trap 'rm -f -- "$sudoers"' EXIT
printf 'fleetdeploy ALL=(root) NOPASSWD: /usr/local/sbin/fleet-flow-deploy\n' > "$sudoers"
visudo -cf "$sudoers"
install -m 440 -o root -g root "$sudoers" /etc/sudoers.d/fleet-flow-deploy
printf 'Konto CI gotowe. Przed wdrożeniem potwierdź DNS, sekrety Actions i reguły portów 80/443.\n'
