function tokenFromHash(hash: string, action: string): string | null {
  if (!hash.startsWith(`#${action}?`)) return null;
  return (
    new URLSearchParams(hash.slice(hash.indexOf("?") + 1)).get("token") || ""
  );
}

export function resetTokenFromHash(hash: string): string | null {
  return tokenFromHash(hash, "reset-password");
}

export function activationTokenFromHash(hash: string): string | null {
  return tokenFromHash(hash, "activate-account");
}

export function emailTokenFromHash(hash: string): string | null {
  return tokenFromHash(hash, "confirm-email");
}
export function validResetToken(token: string) {
  return /^[A-Za-z0-9_-]{20,100}$/.test(token);
}
