import { describe, expect, it } from "vitest";
import {
  BURST_DURATION_MS,
  BURST_MAX_RADIUS_M,
  burstCount,
  burstParticles,
} from "./effects";

describe("decorative burst", () => {
  it("is deterministic for a given seed and age", () => {
    expect(burstParticles(7, 1000, 30)).toEqual(burstParticles(7, 1000, 30));
    expect(burstParticles(7, 1000, 30)).not.toEqual(
      burstParticles(8, 1000, 30),
    );
  });
  it("is empty before impact, after its lifetime, or with zero count", () => {
    expect(burstParticles(1, -1, 10)).toEqual([]);
    expect(burstParticles(1, BURST_DURATION_MS + 1, 10)).toEqual([]);
    expect(burstParticles(1, 100, 0)).toEqual([]);
  });
  it("stays within the radius cap and fades out", () => {
    const early = burstParticles(3, 500, 50);
    const late = burstParticles(3, BURST_DURATION_MS - 1, 50);
    for (const p of late)
      expect(Math.hypot(...p.offset)).toBeLessThanOrEqual(
        BURST_MAX_RADIUS_M + 1,
      );
    expect(late[0]!.alpha).toBeLessThan(early[0]!.alpha);
  });
  it("honours reduced motion and low graphics", () => {
    expect(burstCount({ lowGraphics: false, reducedMotion: true })).toBe(0);
    expect(
      burstCount({ lowGraphics: true, reducedMotion: false }),
    ).toBeLessThan(burstCount({ lowGraphics: false, reducedMotion: false }));
  });
});
