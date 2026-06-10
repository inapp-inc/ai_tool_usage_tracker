import enUS from "./en-US.json";

export type LocaleKey = keyof typeof enUS;

const resources: Record<string, Record<LocaleKey, string>> = {
  "en-US": enUS,
};

export function t(key: LocaleKey, locale = "en-US"): string {
  return resources[locale]?.[key] ?? key;
}
