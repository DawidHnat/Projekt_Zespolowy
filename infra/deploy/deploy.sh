#!/usr/bin/env bash
# Zmienne POSTGRES_* rozwija powłoka kontenera, nie hosta wdrożeniowego.
# shellcheck disable=SC2016
set -Eeuo pipefail
umask 077

[[ $EUID -eq 0 && $# -ge 1 && $1 =~ ^[0-9a-f]{40}$ ]] || {
  printf 'Użycie: root fleet-flow-deploy <40 znaków SHA> ' >&2
  printf '[--allow-rollback], archiwum na stdin.\n' >&2
  exit 1
}

revision=$1
allow_rollback=0
for arg in "${@:2}"; do
  if [[ "$arg" == "--allow-rollback" ]]; then
    allow_rollback=1
  fi
done
if [[ "${FLEET_FLOW_ALLOW_ROLLBACK:-}" =~ ^(1|true|yes)$ ]]; then
  allow_rollback=1
fi

short_revision=${revision:0:7}
base=/opt/fleet-flow
shared="$base/shared"
install -d -m 700 "$base/releases" "$shared/backups"
previous=$(readlink -f "$base/current" || true)

current_commit=""
if [[ -n $previous && -f "$previous/commit" ]]; then
  current_commit=$(cat "$previous/commit")
fi

# Walidacja aktualności wydania PRZED wypakowaniem i PRZED mutacją (SCRUM-137)
scripts_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
validator="/usr/local/sbin/fleet-flow-validate-release"
test -f "$validator" || validator="$scripts_dir/validate_release.py"

validation_cmd=(
  python3 "$validator"
  --target-sha "$revision"
  --repo-dir "$shared/repo.git"
)
if [[ -n "$current_commit" ]]; then
  validation_cmd+=(--current-sha "$current_commit")
fi
if [[ "$allow_rollback" -eq 1 ]]; then
  validation_cmd+=(--allow-rollback)
fi

"${validation_cmd[@]}"

release=$(mktemp -d "$base/releases/$revision.XXXXXX")

# Filtr data odrzuca ścieżki wychodzące poza wydanie, urządzenia i niebezpieczne linki.
python3 -c '
import sys, tarfile
with tarfile.open(fileobj=sys.stdin.buffer, mode="r|gz") as archive:
    archive.extractall(sys.argv[1], filter="data")
' "$release"

test -f "$release/runtime.env" && test ! -L "$release/runtime.env"
grep -Fq "data-build-sha=\"$short_revision\"" "$release/frontend/dist/index.html"
grep -Fq "data-build-sha=\"$short_revision\"" "$release/frontend/dist/status.html"
test -f "$release/infra/deploy/compose.yml"
domain=$(sed -n 's/^APP_DOMAIN=//p' "$release/runtime.env")
[[ $domain =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,}$ ]]
grep -Fq "https://$domain/" "$release/frontend/dist/status.html"
printf '%s\n' "$revision" > "$release/commit"

export FLEET_FLOW_BUILD_SHA="$revision"
export FLEET_FLOW_ENV_FILE="$shared/runtime.env"
dc() {
  docker compose -p fleet-flow --env-file "$FLEET_FLOW_ENV_FILE" \
    -f "$release/infra/deploy/compose.yml" "$@"
}

rollback() {
  result=$?
  trap - ERR
  printf 'Wdrożenie nie przeszło kontroli; nie zatwierdzono nowej wersji.\n' >&2
  if [[ -d "${release:-}" ]]; then
    rm -rf -- "$release"
  fi
  if [[ -n $previous && -f "$previous/commit" && -f "$shared/runtime.env.previous" ]]; then
    cp "$shared/runtime.env.previous" "$FLEET_FLOW_ENV_FILE"
    old_revision=$(cat "$previous/commit")
    if [[ $old_revision =~ ^[0-9a-f]{40}$ ]]; then
      FLEET_FLOW_BUILD_SHA="$old_revision" docker compose -p fleet-flow \
        --env-file "$FLEET_FLOW_ENV_FILE" -f "$previous/infra/deploy/compose.yml" \
        up -d --wait --no-build api web || true
    fi
  else
    dc stop api web || true
  fi
  printf 'Schemat bazy nie jest automatycznie cofany; kopia pozostaje w %s/backups.\n' "$shared" >&2
  exit "$result"
}

test ! -f "$FLEET_FLOW_ENV_FILE" || cp "$FLEET_FLOW_ENV_FILE" "$shared/runtime.env.previous"
install -m 600 "$release/runtime.env" "$FLEET_FLOW_ENV_FILE"
rm -- "$release/runtime.env"
# extractall respektuje umask; kod i statyczne pliki muszą być czytelne
# także dla nieuprzywilejowanego użytkownika obrazu API.
chmod -R u=rwX,go=rX "$release"
trap rollback ERR

dc config --quiet
dc up -d --wait database
backup="$shared/backups/before-$revision-$(date +%s).dump"
dc exec -T database sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$backup"

# Rzeczywista próba odtworzenia do osobnej tymczasowej bazy, bez zmiany bazy aplikacji.
restore_database="fleet_flow_restore_$(date +%s)_$$"
dc exec -T database sh -c 'createdb -U "$POSTGRES_USER" "$1"' sh "$restore_database"
restore_cmd='pg_restore --exit-on-error --no-owner -U "$POSTGRES_USER" -d "$1"'
if dc exec -T database sh -c "$restore_cmd" sh "$restore_database" < "$backup"; then
  dc exec -T database sh -c 'dropdb -U "$POSTGRES_USER" "$1"' sh "$restore_database"
else
  dc exec -T database sh -c 'dropdb -U "$POSTGRES_USER" "$1"' sh "$restore_database" || true
  false
fi

dc build api
dc run --rm --no-deps api python -m alembic upgrade head
dc up -d --wait api web
curl --fail --silent --show-error --max-time 10 http://127.0.0.1/ \
  | grep -F "data-build-sha=\"$short_revision\""
curl --fail --silent --show-error --retry 12 --retry-delay 5 --retry-all-errors \
  --retry-max-time 180 --max-time 15 "https://$domain/api/health/ready" >/dev/null

ln -s "$release" "$base/.current-$revision"
mv -Tf "$base/.current-$revision" "$base/current"
trap - ERR
printf 'Wdrożono %s; kopia i próba odtworzenia: OK.\n' "$revision"
