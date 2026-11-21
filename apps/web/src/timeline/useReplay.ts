import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createClock,
  pause as pauseClock,
  play as playClock,
  reset as resetClock,
  seek as seekClock,
  setSpeed as setClockSpeed,
  tick,
  type ClockState,
} from "./clock";
import {
  interpolateFrames,
  sampleTimes,
  type FrameSample,
  type Vec3,
} from "./interpolation";

export type Replay = {
  clock: ClockState;
  positions: Map<string, Vec3>;
  play: () => void;
  pause: () => void;
  reset: () => void;
  seek: (timeMs: number) => void;
  setSpeed: (speed: number) => void;
};

/**
 * Drives the deterministic clock from requestAnimationFrame. Wall-clock deltas
 * are capped so a background tab cannot jump the replay forward.
 */
export function useReplay(samples: readonly FrameSample[]): Replay {
  const times = useMemo(() => sampleTimes(samples), [samples]);
  const start = times[0] ?? 0;
  const end = times[times.length - 1] ?? 0;
  const [clock, setClock] = useState(() => createClock(start, end));

  useEffect(() => setClock(createClock(start, end)), [start, end]);

  const playing = clock.playing;
  const last = useRef(0);
  useEffect(() => {
    if (!playing) return;
    let frame = 0;
    let pending = 0;
    last.current = performance.now();
    const step = (now: number) => {
      pending += Math.min(now - last.current, 100);
      last.current = now;
      // Throttle React updates to ~30 Hz; accumulated time keeps replay exact.
      if (pending >= 33) {
        const delta = pending;
        pending = 0;
        setClock((current) => tick(current, delta));
      }
      frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [playing]);

  const positions = useMemo(
    () => interpolateFrames(samples, times, clock.timeMs),
    [samples, times, clock.timeMs],
  );

  return {
    clock,
    positions,
    play: useCallback(() => setClock(playClock), []),
    pause: useCallback(() => setClock(pauseClock), []),
    reset: useCallback(() => setClock(resetClock), []),
    seek: useCallback((t: number) => setClock((c) => seekClock(c, t)), []),
    setSpeed: useCallback(
      (s: number) => setClock((c) => setClockSpeed(c, s)),
      [],
    ),
  };
}
