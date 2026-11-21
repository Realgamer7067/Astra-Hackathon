import type { CesiumWidget } from "cesium";

/**
 * Value for CesiumWidget.resolutionScale. With useBrowserRecommendedResolution
 * disabled Cesium renders at devicePixelRatio x resolutionScale, so the scale
 * is a multiplier on top of the device ratio, not the ratio itself. Target
 * effective ratio: device pixel ratio capped at 2 (native sharpness); 1 CSS
 * pixel per pixel on low graphics.
 */
export function renderScale(lowGraphics: boolean, dpr?: number): number {
  const raw =
    dpr ?? (typeof window === "undefined" ? 1 : window.devicePixelRatio);
  const ratio = Number.isFinite(raw) && raw > 0 ? raw : 1;
  const target = lowGraphics ? 1 : Math.min(Math.max(ratio, 1), 2);
  return target / ratio;
}
/** Frames-per-second from frame timestamps over a window, or null if too few. */
export function fpsFromFrames(timesMs: readonly number[]): number | null {
  if (timesMs.length < 2) return null;
  const span = timesMs[timesMs.length - 1]! - timesMs[0]!;
  return span > 0 ? Math.round(((timesMs.length - 1) * 1000) / span) : null;
}

/**
 * Measures actual rendered frames (postRender) and writes the result to a DOM
 * node about twice a second, avoiding React updates. With requestRenderMode the
 * scene only renders on change, so an idle scene reports "idle".
 */
export function trackFps(
  widget: CesiumWidget,
  label: HTMLElement | null,
): () => void {
  const times: number[] = [];
  const onFrame = () => {
    const now = performance.now();
    times.push(now);
    while (times.length > 1 && now - times[0]! > 1000) times.shift();
  };
  const remove = widget.scene.postRender.addEventListener(onFrame);
  const timer = window.setInterval(() => {
    if (!label) return;
    const fresh =
      times.length > 0 && performance.now() - times[times.length - 1]! < 1000;
    const fps = fresh ? fpsFromFrames(times) : null;
    label.textContent = fps === null ? "FPS idle" : `${fps} FPS`;
  }, 500);
  return () => {
    remove();
    window.clearInterval(timer);
  };
}
