#!/usr/bin/env bash
set -euo pipefail

# Jedyny dozwolony rozkaz dedykowanego klucza CI; bez interaktywnej powłoki.
if [[ ${SSH_ORIGINAL_COMMAND:-} =~ ^deploy\ ([0-9a-f]{40})$ ]]; then
  exec sudo -n /usr/local/sbin/fleet-flow-deploy "${BASH_REMATCH[1]}"
fi
printf 'Dozwolone: deploy <40 znaków SHA>.\n' >&2
exit 1
