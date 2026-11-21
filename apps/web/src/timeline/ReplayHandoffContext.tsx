import { createContext, useContext } from "react";
import {
  emitScenarioCompleted,
  type ScenarioCompletionCallback,
} from "./scenarioHandoff";

/**
 * Supplies the replay session's completion callback to any panel mounted
 * inside <App> (for example TASK-003's ScenarioLab) without prop drilling.
 * Outside a provider it falls back to the typed window event, so a panel that
 * calls it always reaches the replay session.
 */
export const ReplayHandoffContext = createContext<ScenarioCompletionCallback>(
  (input) => {
    emitScenarioCompleted(input);
  },
);

/**
 * Returns the callback a collision panel should call once its job reaches
 * state === "completed", passing the job's scenario ID, seed and any impact
 * metadata:
 *
 *   const onCompleted = useScenarioCompletion();
 *   onCompleted({ job, epoch_utc, impact_position_itrs_m });
 */
export function useScenarioCompletion(): ScenarioCompletionCallback {
  return useContext(ReplayHandoffContext);
}
