import { SPEEDS, type ClockState } from "./clock";
import type { Replay } from "./useReplay";

const format = (ms: number) =>
  `${new Date(ms).toISOString().slice(0, 19).replace("T", " ")} UTC`;

type Props = { replay: Replay; label?: string };

export default function TimelineControls({ replay, label }: Props) {
  const { clock } = replay;
  const empty = clock.endMs === clock.startMs;
  return (
    <section className="timeline" aria-label="Replay timeline">
      <div className="timeline-buttons">
        <button
          onClick={clock.playing ? replay.pause : replay.play}
          disabled={empty}
          aria-label={clock.playing ? "Pause replay" : "Play replay"}
        >
          {clock.playing ? "Pause" : "Play"}
        </button>
        <button onClick={replay.reset} disabled={empty}>
          Reset
        </button>
        <label>
          Speed
          <select
            value={clock.speed}
            onChange={(e) => replay.setSpeed(Number(e.target.value))}
          >
            {SPEEDS.map((s) => (
              <option key={s} value={s}>
                {s}×
              </option>
            ))}
          </select>
        </label>
      </div>
      <input
        type="range"
        aria-label="Replay position"
        min={clock.startMs}
        max={clock.endMs}
        step={Math.max(1, (clock.endMs - clock.startMs) / 1000)}
        value={clock.timeMs}
        disabled={empty}
        onChange={(e) => replay.seek(Number(e.target.value))}
        aria-valuetext={format(clock.timeMs)}
      />
      <output aria-live="off">
        {empty ? "No replay frames loaded" : format(clock.timeMs)}
        {label ? ` · ${label}` : ""}
      </output>
    </section>
  );
}

export type { ClockState };
