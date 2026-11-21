import type { ReactNode } from "react";
import type { useReplaySession } from "../app/useReplaySession";
import TimelineControls from "./TimelineControls";

type Props = {
  session: ReturnType<typeof useReplaySession>;
  previewing: boolean;
  onPreviewChange: (previewing: boolean) => void;
  lowGraphics: boolean;
  onLowGraphicsChange: (lowGraphics: boolean) => void;
  onRetry: () => void;
  children?: ReactNode;
};

export default function ReplayBar({
  session,
  previewing,
  onPreviewChange,
  lowGraphics,
  onLowGraphicsChange,
  onRetry,
  children,
}: Props) {
  return (
    <div className="replay-bar">
      <label className="preview-toggle">
        <input
          type="checkbox"
          checked={previewing}
          onChange={(e) => onPreviewChange(e.target.checked)}
        />
        Synthetic replay preview
      </label>
      {previewing ? (
        <p className="synthetic-badge" role="note">
          SYNTHETIC DEMO: illustrative motion, not a simulation result
        </p>
      ) : session.framesState.status === "loading" ? (
        <p className="effect-note" role="status">
          Loading replay frames…
        </p>
      ) : session.framesState.status === "error" ? (
        <div className="failure">
          <p role="alert">
            Replay frames unavailable. {session.framesState.message}
          </p>
          <button
            onClick={() => {
              session.retryFrames();
              onRetry();
            }}
          >
            Retry
          </button>
        </div>
      ) : session.framesState.status === "empty" ? (
        <p className="effect-note" role="status">
          No replay frames in this run
          {session.provenance ? ` (${session.provenance.kind})` : ""}. Nothing
          to replay yet.
        </p>
      ) : (
        <p className="synthetic-badge" role="note">
          Replay frames: {session.provenance?.kind} · {session.provenance?.mode}
          {session.provenance?.kind === "HYPOTHETICAL_SIMULATION"
            ? " · HYPOTHETICAL SCENARIO, NOT A PREDICTION"
            : ""}
        </p>
      )}
      {session.replayable && (
        <>
          <p className="effect-note">
            Impact flash is a decorative effect, not simulated debris.
          </p>
          <div className="timeline-buttons">
            <button onClick={session.focusImpact} disabled={!session.hasImpact}>
              Focus collision
            </button>
            <label className="preview-toggle">
              <input
                type="checkbox"
                checked={lowGraphics}
                onChange={(e) => onLowGraphicsChange(e.target.checked)}
              />
              Low graphics
            </label>
          </div>
          <TimelineControls
            replay={session.replay}
            label={previewing ? "synthetic" : session.provenance?.kind}
          />
        </>
      )}
      {children}
    </div>
  );
}
