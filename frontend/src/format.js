// Numbers aur dates har jagah ek jaise dikhein

export const mw = (v) => `${Math.round(v).toLocaleString("en-GB")} MW`;

export const signedMw = (v) => `${v > 0 ? "+" : ""}${mw(v)}`;

// Data UTC mein hai, trader UK time mein sochta hai
export const ukDateTime = (iso) =>
  new Date(iso).toLocaleString("en-GB", {
    timeZone: "Europe/London",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

export const ukDay = (iso) =>
  new Date(iso).toLocaleDateString("en-GB", {
    timeZone: "Europe/London",
    day: "2-digit",
    month: "short",
  });