#!/usr/bin/env bash
# Uruchom na VPS jako root, wskazując katalog zatwierdzonych kluczy publicznych.
# Ten etap przygotowuje konta. Zabezpieczenie SSH wykonujemy po teście drugiej sesji.
set -euo pipefail
umask 077

if [[ $EUID -ne 0 || $# -ne 1 ]]; then
  printf 'Użycie na VPS: sudo bash setup-accounts.sh /katalog/public-keys\n' >&2
  exit 1
fi

key_dir=$(realpath -- "$1")
members=(jczaja51 dawidhnat jnazarewiczs mglowacki0)
[[ -f "$key_dir/jczaja51.pub" ]] || {
  printf 'Brakuje klucza administratora jczaja51.pub. Nie zmieniono kont.\n' >&2
  exit 1
}

# Sprawdź wszystkie dostarczone pliki i istniejące konta przed pierwszą zmianą.
for member in "${members[@]}"; do
  key_file="$key_dir/$member.pub"
  if [[ -f "$key_file" ]]; then
    awk 'NF { n++; if ($1 !~ /^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521))$/) bad=1 }
      END { exit (n != 1 || bad) }' "$key_file" || {
      printf 'Nieprawidłowy plik publiczny: %s\n' "$key_file" >&2
      exit 1
    }
    ssh-keygen -lf "$key_file"
  fi
  if id "$member" >/dev/null 2>&1; then
    [[ $(id -u "$member") -ge 1000 ]] &&
      [[ $(getent passwd "$member" | cut -d: -f6) == "/home/$member" ]] || {
      printf 'Istniejące konto %s wymaga ręcznego sprawdzenia.\n' "$member" >&2
      exit 1
    }
  fi
done

groupadd -f fleet-flow
for member in "${members[@]}"; do
  if ! id "$member" >/dev/null 2>&1; then
    useradd --create-home --user-group --shell /bin/bash "$member"
  fi
  usermod -aG fleet-flow "$member"
  passwd -l "$member" >/dev/null
  primary_group=$(id -gn "$member")
  install -d -m 700 -o "$member" -g "$primary_group" "/home/$member/.ssh"
  key_file="$key_dir/$member.pub"
  if [[ -f "$key_file" ]]; then
    authorized_keys="/home/$member/.ssh/authorized_keys"
    touch "$authorized_keys"
    chown "$member:$primary_group" "$authorized_keys"
    chmod 600 "$authorized_keys"
    key_line=$(awk 'NF { print; exit }' "$key_file")
    if ! grep -qxF -- "$key_line" "$authorized_keys"; then
      # Osobny separator chroni istniejącą ostatnią linię bez znaku nowej linii.
      printf '\n%s\n' "$key_line" >> "$authorized_keys"
    fi
    printf '%s: klucz zainstalowany; logowanie wymaga testu właściciela.\n' "$member"
  else
    printf '%s: konto przygotowane; brak nowego klucza publicznego.\n' "$member"
  fi
done

install -d -o root -g fleet-flow -m 2770 /srv/fleet-flow
sudoers_file=$(mktemp)
trap 'rm -f -- "$sudoers_file"' EXIT
printf 'jczaja51 ALL=(ALL) NOPASSWD:ALL\ndawidhnat ALL=(ALL) NOPASSWD:ALL\n' > "$sudoers_file"
visudo -cf "$sudoers_file"
install -o root -g root -m 440 "$sudoers_file" /etc/sudoers.d/fleet-flow-admins
printf 'Następny krok: druga sesja SSH jczaja51 i test sudo; następnie zabezpieczenie SSH.\n'
