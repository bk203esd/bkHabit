(() => {
  const csrfToken = document.querySelector("meta[name='csrf-token']")?.content;
  const dueUrl = document.body.dataset.alarmsDueUrl;
  const ackUrlTemplate = document.body.dataset.alarmsAckUrl;
  if (!dueUrl || !ackUrlTemplate) return;

  const notified = new Set();

  async function ensurePermission() {
    if (!("Notification" in window)) return false;
    if (Notification.permission === "granted") return true;
    if (Notification.permission === "denied") return false;
    const result = await Notification.requestPermission();
    return result === "granted";
  }

  async function ackAlarm(id) {
    const url = ackUrlTemplate.replace("999999", String(id));
    await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken || "",
      },
    });
  }

  async function poll() {
    try {
      const allowed = await ensurePermission();
      if (!allowed) return;

      const response = await fetch(dueUrl, { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      const data = await response.json();
      for (const alarm of data.alarms || []) {
        const key = `${alarm.id}-${alarm.time}`;
        if (notified.has(key)) continue;
        notified.add(key);
        const notification = new Notification(alarm.title || "DayFlow alarm", {
          body: `Alarm at ${alarm.time}`,
          tag: key,
        });
        notification.onclick = () => window.focus();
        await ackAlarm(alarm.id);
      }
    } catch (error) {
      // Silent fail; next poll will retry.
    }
  }

  // Prime permission on first user gesture if needed.
  document.addEventListener(
    "click",
    () => {
      ensurePermission();
    },
    { once: true }
  );

  poll();
  setInterval(poll, 20000);
})();
