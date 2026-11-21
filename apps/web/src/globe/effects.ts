/**
 * Decorative impact flash. A pure function of (seed, age): it never reads or
 * writes simulation state, so it cannot change numerical output. It is NOT
 * simulated debris and must be labelled as illustrative wherever it is shown.
 */
export const BURST_DURATION_MS = 4000;
export const BURST_MAX_RADIUS_M = 400_000;

export type BurstParticle = {
  offset: [number, number, number];
  /** 0 (invisible) to 1 (full). */
  alpha: number;
};

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function burstParticles(
  seed: number,
  ageMs: number,
  count: number,
): BurstParticle[] {
  if (!(ageMs >= 0) || ageMs > BURST_DURATION_MS || count <= 0) return [];
  const life = ageMs / BURST_DURATION_MS;
  const ease = 1 - (1 - life) ** 3;
  const random = mulberry32(seed);
  const particles: BurstParticle[] = [];
  for (let i = 0; i < count; i++) {
    // Uniform direction on a sphere.
    const z = random() * 2 - 1;
    const phi = random() * Math.PI * 2;
    const r = Math.sqrt(1 - z * z);
    const reach = (0.35 + 0.65 * random()) * BURST_MAX_RADIUS_M * ease;
    particles.push({
      offset: [r * Math.cos(phi) * reach, r * Math.sin(phi) * reach, z * reach],
      alpha: (1 - life) ** 1.5,
    });
  }
  return particles;
}

/** Particle count by graphics setting; reduced motion disables the burst. */
export function burstCount(options: {
  lowGraphics: boolean;
  reducedMotion: boolean;
}): number {
  if (options.reducedMotion) return 0;
  return options.lowGraphics ? 24 : 120;
}
