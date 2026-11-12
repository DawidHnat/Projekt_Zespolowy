// Only announce that the shared cookie changed. Each tab reads its own /auth/me.
const channelName = "fleet-flow.session-change.v1";

export function listenForSessionChanges(onChange: () => void) {
  if (typeof BroadcastChannel === "function") {
    const channel = new BroadcastChannel(channelName);
    channel.onmessage = onChange;
    return {
      notify: () => channel.postMessage(null),
      close: () => channel.close(),
    };
  }

  const onStorage = (event: StorageEvent) => {
    if (event.key === channelName && event.newValue === "changed") onChange();
  };
  window.addEventListener("storage", onStorage);
  return {
    notify: () => {
      try {
        localStorage.setItem(channelName, "changed");
        localStorage.removeItem(channelName);
      } catch {
        // A tab with neither transport still checks the server on protected requests.
      }
    },
    close: () => window.removeEventListener("storage", onStorage),
  };
}
