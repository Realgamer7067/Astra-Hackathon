import { useEffect, useRef, useState } from "react";
import {
  Cartesian3,
  Cartographic,
  CesiumWidget,
  Color,
  Credit,
  CreditDisplay,
  GeographicTilingScheme,
  ImageryLayer,
  Material,
  PointPrimitive,
  PointPrimitiveCollection,
  PolylineCollection,
  type Primitive,
  TileMapServiceImageryProvider,
  UrlTemplateImageryProvider,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { burstCount, burstParticles } from "./effects";
import type { EntryCrossing } from "../features/results/api";
import type { Vec3 } from "../timeline/interpolation";
import type { EntryCell, FragmentTrack } from "../timeline/entryReplay";
import {
  drawTracks,
  entryHeatmap,
  entryPosition,
  focusReplay,
} from "./replayLayers";
import {
  type CartesianState,
  type CatalogObject,
  kindColors,
} from "../app/demo";

type Props = {
  states?: CartesianState[];
  objects?: CatalogObject[];
  selectedId: string | null;
  /** Interpolated replay positions (ITRS metres). */
  replayPositions?: Map<string, [number, number, number]>;
  /** Impact site (ITRS metres) and time since impact; null age = not started. */
  impact?: {
    position: [number, number, number];
    ageMs: number | null;
    seed: number;
  };
  /** Increment to fly the camera to the impact site. */
  focusToken?: number;
  tracks?: FragmentTrack[];
  entryCells?: EntryCell[];
  entryFocus?: EntryCrossing;
  approach?: readonly { position: Vec3 }[];
  onApproachComplete: () => void;
  lowGraphics?: boolean;
};

import { renderScale, trackFps } from "./quality";

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function reset(widget: CesiumWidget) {
  widget.camera.setView({
    destination: Cartesian3.fromDegrees(65, 23, 18_000_000),
  });
  widget.scene.requestRender();
}

export default function EarthView({
  states,
  objects,
  selectedId,
  replayPositions,
  impact,
  focusToken,
  tracks,
  entryCells,
  entryFocus,
  approach,
  onApproachComplete,
  lowGraphics = false,
}: Props) {
  const fpsLabel = useRef<HTMLSpanElement>(null);
  const burstCollection = useRef<PointPrimitiveCollection | null>(null);
  const replayCollection = useRef<PointPrimitiveCollection | null>(null);
  const trailLines = useRef<PolylineCollection | null>(null);
  const entryLines = useRef<PolylineCollection | null>(null);
  const heatLayer = useRef<Primitive | null>(null);
  const approachPoints = useRef<PointPrimitiveCollection | null>(null);
  const approachComplete = useRef(onApproachComplete);
  approachComplete.current = onApproachComplete;
  const replayPoints = useRef<Map<string, PointPrimitive>>(new Map());
  const lastFocusToken = useRef(0);
  const host = useRef<HTMLDivElement>(null);
  const widget = useRef<CesiumWidget | null>(null);
  const points = useRef<PointPrimitiveCollection | null>(null);
  const [available, setAvailable] = useState(false);
  const [warning, setWarning] = useState<string | null>(null);

  useEffect(() => {
    if (!host.current) return;
    let instance: CesiumWidget;
    try {
      CreditDisplay.cesiumCredit = new Credit("CesiumJS");
      instance = new CesiumWidget(host.current, {
        baseLayer: false,
        skyBox: false,
        scene3DOnly: true,
        requestRenderMode: true,
        // Render at device resolution (capped) instead of CSS pixels so the
        // globe and markers are crisp on high-DPI displays.
        useBrowserRecommendedResolution: false,
        showRenderLoopErrors: false,
      });
    } catch {
      setWarning("Earth view needs WebGL 2. The catalog remains available.");
      return;
    }
    widget.current = instance;
    instance.resolutionScale = renderScale(false);
    instance.scene.postProcessStages.fxaa.enabled = true;
    const stopFps = trackFps(instance, fpsLabel.current);
    instance.scene.backgroundColor = Color.fromCssColorString("#090f17");
    if (instance.scene.globe)
      instance.scene.globe.baseColor = Color.fromCssColorString("#22455e");
    points.current = instance.scene.primitives.add(
      new PointPrimitiveCollection(),
    );
    replayCollection.current = instance.scene.primitives.add(
      new PointPrimitiveCollection(),
    );
    burstCollection.current = instance.scene.primitives.add(
      new PointPrimitiveCollection(),
    );
    trailLines.current = instance.scene.primitives.add(
      new PolylineCollection(),
    );
    entryLines.current = instance.scene.primitives.add(
      new PolylineCollection(),
    );
    approachPoints.current = instance.scene.primitives.add(
      new PointPrimitiveCollection(),
    );
    reset(instance);
    setAvailable(true);
    const removeError = instance.scene.renderError.addEventListener(() => {
      setAvailable(false);
      setWarning("Earth view stopped rendering. Reload the page to try again.");
    });
    const imagery = new UrlTemplateImageryProvider({
      url: "/blue-marble/{z}/{x}/{y}.webp",
      tilingScheme: new GeographicTilingScheme(),
      tileWidth: 512,
      tileHeight: 512,
      maximumLevel: 3,
      hasAlphaChannel: false,
      enablePickFeatures: false,
      credit: new Credit(
        '<a href="https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-topography-bathymetry/" target="_blank" rel="noopener noreferrer">NASA Earth Observatory · Blue Marble</a>',
        true,
      ),
    });
    const layer = new ImageryLayer(imagery);
    const removeImageryError = imagery.errorEvent.addEventListener(() => {
      if (instance.isDestroyed() || !instance.scene.imageryLayers.remove(layer))
        return;
      TileMapServiceImageryProvider.fromUrl(
        "/cesium/Assets/Textures/NaturalEarthII",
        { credit: new Credit("Natural Earth", true) },
      )
        .then((fallback) => {
          if (instance.isDestroyed()) return;
          instance.scene.imageryLayers.add(new ImageryLayer(fallback));
          instance.scene.requestRender();
        })
        .catch(() => {
          if (!instance.isDestroyed())
            setWarning(
              "Local imagery unavailable. Showing the Earth ellipsoid.",
            );
        });
    });
    instance.scene.imageryLayers.add(layer);
    instance.scene.requestRender();
    return () => {
      stopFps();
      removeError();
      removeImageryError();
      approachPoints.current = null;
      trailLines.current = null;
      entryLines.current = null;
      heatLayer.current = null;
      points.current = null;
      replayCollection.current = null;
      burstCollection.current = null;
      replayPoints.current.clear();
      widget.current = null;
      instance.destroy();
    };
  }, []);

  useEffect(() => {
    const collection = points.current;
    if (!collection) return;
    collection.removeAll();
    const catalog = new Map(objects?.map((object) => [object.id, object.kind]));
    for (const sample of states ?? []) {
      const selected = sample.object_id === selectedId;
      collection.add({
        position: Cartesian3.fromArray(sample.position),
        color: Color.fromCssColorString(
          kindColors[catalog.get(sample.object_id) ?? "UNKNOWN"],
        ),
        pixelSize: selected ? 12 : 7,
        outlineColor: selected
          ? Color.WHITE
          : Color.fromCssColorString("#101e28"),
        outlineWidth: selected ? 2 : 1,
      });
    }
    widget.current?.scene.requestRender();
  }, [states, objects, selectedId]);

  useEffect(() => {
    const instance = widget.current;
    const selected = states?.find((sample) => sample.object_id === selectedId);
    if (!instance || !selected) return;
    const coordinates = Cartographic.fromCartesian(
      Cartesian3.fromArray(selected.position),
    );
    instance.camera.setView({
      destination: Cartesian3.fromRadians(
        coordinates.longitude,
        coordinates.latitude,
        18_000_000,
      ),
    });
    instance.scene.requestRender();
  }, [states, selectedId]);

  useEffect(() => {
    const collection = replayCollection.current;
    const live = replayPoints.current;
    if (!collection) return;
    for (const [id, point] of live) {
      if (!replayPositions?.has(id)) {
        collection.remove(point);
        live.delete(id);
      }
    }
    for (const [id, position] of replayPositions ?? []) {
      const cartesian = Cartesian3.fromArray(position);
      const existing = live.get(id);
      if (existing) existing.position = cartesian;
      else
        live.set(
          id,
          collection.add({
            position: cartesian,
            color: Color.fromCssColorString("#ffb454"),
            pixelSize: 8,
            outlineColor: Color.WHITE,
            outlineWidth: 1,
          }),
        );
    }
    widget.current?.scene.requestRender();
  }, [replayPositions]);

  useEffect(() => {
    const instance = widget.current;
    if (!instance) return;
    instance.resolutionScale = renderScale(lowGraphics);
    // FXAA already smooths edges; MSAA on top is redundant cost on low graphics.
    instance.scene.msaaSamples = lowGraphics ? 1 : 4;
    instance.scene.requestRender();
  }, [lowGraphics]);

  // Decorative burst: independent of physics; off under reduced motion.
  useEffect(() => {
    const collection = burstCollection.current;
    if (!collection) return;
    collection.removeAll();
    const count = burstCount({
      lowGraphics,
      reducedMotion: prefersReducedMotion(),
    });
    if (impact && impact.ageMs !== null && count > 0) {
      const origin = Cartesian3.fromArray(impact.position);
      for (const p of burstParticles(impact.seed, impact.ageMs, count)) {
        collection.add({
          position: Cartesian3.add(
            origin,
            Cartesian3.fromArray(p.offset),
            new Cartesian3(),
          ),
          color: Color.fromCssColorString("#ffb454").withAlpha(p.alpha),
          pixelSize: 3,
        });
      }
    }
    widget.current?.scene.requestRender();
  }, [impact, lowGraphics]);

  useEffect(() => {
    if (!trailLines.current) return;
    drawTracks(trailLines.current, tracks ?? []);
    widget.current?.scene.requestRender();
  }, [tracks]);

  useEffect(() => {
    const instance = widget.current;
    if (!instance) return;
    if (heatLayer.current) {
      instance.scene.primitives.remove(heatLayer.current);
      heatLayer.current = null;
    }
    if (entryCells?.length) {
      heatLayer.current = instance.scene.primitives.add(
        entryHeatmap(entryCells),
      );
    }
    instance.scene.requestRender();
  }, [entryCells]);

  useEffect(() => {
    const instance = widget.current;
    const lines = entryLines.current;
    if (!instance || !lines || !available) return;
    lines.removeAll();
    if (entryFocus) {
      const point = entryPosition(entryFocus);
      const surface = Cartesian3.fromDegrees(
        entryFocus.longitude_deg,
        entryFocus.latitude_deg,
        3_000,
      );
      lines.add({
        positions: [surface, point],
        width: 4,
        material: Material.fromType("PolylineGlow", {
          color: Color.ORANGE,
          glowPower: 0.25,
        }),
      });
      focusReplay(instance.camera, point, prefersReducedMotion() ? 0 : 1.25);
    }
    instance.scene.requestRender();
  }, [available, entryFocus]);

  const contact = impact?.position;
  useEffect(() => {
    const points = approachPoints.current;
    const instance = widget.current;
    if (!available || !instance || !points || !approach || !contact) return;
    const target = Cartesian3.fromArray(contact);
    const actors = approach.map(({ position }, index) => {
      const start = Cartesian3.fromArray(position);
      const color = index === 0 ? Color.CYAN : Color.ORANGE;
      return {
        start,
        marker: points.add({
          position: start,
          color,
          pixelSize: 14,
          outlineColor: Color.WHITE,
          outlineWidth: 2,
        }),
      };
    });
    const duration = prefersReducedMotion() ? 1 : 2100;
    let frame = 0;
    const started = performance.now();
    const advance = (now: number) => {
      const t = Math.min(1, (now - started) / duration);
      for (const actor of actors) {
        actor.marker.position = Cartesian3.lerp(
          actor.start,
          target,
          t,
          new Cartesian3(),
        );
      }
      instance.scene.requestRender();
      if (t < 1) frame = requestAnimationFrame(advance);
      else approachComplete.current();
    };
    frame = requestAnimationFrame(advance);
    return () => {
      cancelAnimationFrame(frame);
      if (!points.isDestroyed()) points.removeAll();
    };
  }, [available, approach, contact]);

  // Keep the collision in a three-quarter view so trails have visible depth.
  useEffect(() => {
    const instance = widget.current;
    if (!instance || !available || !impact || !focusToken) return;
    if (lastFocusToken.current === focusToken) return;
    lastFocusToken.current = focusToken;
    focusReplay(
      instance.camera,
      impact.position,
      prefersReducedMotion() ? 0 : 1.4,
    );
    instance.scene.requestRender();
  }, [focusToken, available, impact]);

  function zoom(direction: "in" | "out") {
    const instance = widget.current;
    if (!instance) return;
    const distance = Math.max(
      1000,
      instance.camera.positionCartographic.height * 0.2,
    );
    if (direction === "in") instance.camera.zoomIn(distance);
    else instance.camera.zoomOut(distance);
    instance.scene.requestRender();
  }

  return (
    <>
      <div
        ref={host}
        className="earth-canvas"
        aria-label="Interactive Earth globe"
      />
      {warning && (
        <p className="globe-state" role="status">
          {warning}
        </p>
      )}
      <span
        ref={fpsLabel}
        className="fps-counter"
        role="status"
        aria-label="Rendering frame rate"
      >
        FPS idle
      </span>
      {available && (
        <div
          className="camera-controls"
          role="group"
          aria-label="Globe controls"
        >
          <button aria-label="Zoom in" onClick={() => zoom("in")}>
            +
          </button>
          <button aria-label="Zoom out" onClick={() => zoom("out")}>
            −
          </button>
          <button onClick={() => widget.current && reset(widget.current)}>
            Reset view
          </button>
        </div>
      )}
    </>
  );
}
