// INERT NEGATIVE SECURITY PROBE. Never import, execute or merge.
export function unsafeProbe(untrusted: string) {
  return eval(untrusted);
}
