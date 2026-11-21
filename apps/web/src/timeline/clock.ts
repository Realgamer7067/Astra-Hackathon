/**
 * Deterministic replay clock. Pure functions only: the same inputs always give
 * the same state, and replay never feeds back into the numerical simulation.
 */
export const SPEEDS = [1, 5, 15, 60, 300] as const;

export type ClockState = {
  startMs: number;
  endMs: number;
  timeMs: number;
  speed: number;
  playing: boolean;
};

export function createClock(startMs: number, endMs: number): ClockState {
  if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs < startMs)
    throw new RangeError("Clock interval must be finite with end >= start");
  return { startMs, endMs, timeMs: startMs, speed: 1, playing: false };
}

const clamp = (value: number, low: number, high: number) =>
  Math.min(high, Math.max(low, value));

export const atEnd = (clock: ClockState) => clock.timeMs >= clock.endMs;

export function play(clock: ClockState): ClockState {
  // Pressing play at the end restarts from the beginning.
  const timeMs = atEnd(clock) ? clock.startMs : clock.timeMs;
  return { ...clock, timeMs, playing: clock.endMs > clock.startMs };
}

export const pause = (clock: ClockState): ClockState => ({
  ...clock,
  playing: false,
});

export const reset = (clock: ClockState): ClockState => ({
  ...clock,
  timeMs: clock.startMs,
  playing: false,
});

export function seek(clock: ClockState, timeMs: number): ClockState {
  if (!Number.isFinite(timeMs)) return clock;
  return { ...clock, timeMs: clamp(timeMs, clock.startMs, clock.endMs) };
}

export function setSpeed(clock: ClockState, speed: number): ClockState {
  if (!Number.isFinite(speed) || speed <= 0) return clock;
  return { ...clock, speed };
}

/** Advance by elapsed wall-clock milliseconds; pauses on reaching the end. */
export function tick(clock: ClockState, wallDeltaMs: number): ClockState {
  if (!clock.playing || !(wallDeltaMs > 0)) return clock;
  const timeMs = Math.min(
    clock.endMs,
    clock.timeMs + wallDeltaMs * clock.speed,
  );
  return { ...clock, timeMs, playing: timeMs < clock.endMs };
}

export const progress = (clock: ClockState): number =>
  clock.endMs === clock.startMs
    ? 1
    : (clock.timeMs - clock.startMs) / (clock.endMs - clock.startMs);
