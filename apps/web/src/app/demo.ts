import type { components } from "../../../../packages/contracts/api";

export type DemoBundle = components["schemas"]["DemoBundle"];
export type CatalogObject = components["schemas"]["CatalogObject"];
export type CartesianState = components["schemas"]["CartesianState"];

export const kindLabels: Record<CatalogObject["kind"], string> = {
  PAYLOAD: "Satellite",
  DEBRIS: "Debris",
  ROCKET_BODY: "Rocket body",
  UNKNOWN: "Unknown",
};
export const kindColors: Record<CatalogObject["kind"], string> = {
  PAYLOAD: "#79e3dc",
  DEBRIS: "#f3c17d",
  ROCKET_BODY: "#c6b2e8",
  UNKNOWN: "#c8d2e0",
};

export function utcLabel(epoch: string): string {
  return `${new Date(epoch).toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

export async function loadDemo(signal: AbortSignal): Promise<DemoBundle> {
  const response = await fetch("/api/v1/demo", { signal });
  if (!response.ok) throw new Error("Demo API unavailable");
  return (await response.json()) as DemoBundle;
}
