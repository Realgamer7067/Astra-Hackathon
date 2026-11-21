import { useEffect, useRef, useState } from "react";
import {
  Cartesian3,
  Cartographic,
  CesiumWidget,
  Color,
  Credit,
  CreditDisplay,
  DirectionalLight,
  GeographicTilingScheme,
  HeadingPitchRange,
  LabelCollection,
  ImageryLayer,
  Material,
  Matrix4,
  PointPrimitive,
  PointPrimitiveCollection,
  PolylineCollection,
  SingleTileImageryProvider,
  type Primitive,
  TileMapServiceImageryProvider,
  Transforms,
  UrlTemplateImageryProvider,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { showApproach, type ApproachBody } from "./approachActors";
import { burstCount, burstParticles } from "./effects";
import type { EntryCrossing } from "../features/results/api";
import type { EntryCell, FragmentTrack } from "../timeline/entryReplay";
import {
  drawTracks,
  entryHeatmap,
  entryCellLabel,
  focusEntryOverview,
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
  entryOverview?: EntryCell[];
  collisionCue?: boolean;
  followDebris?: boolean;
  approach?: readonly [ApproachBody, ApproachBody];
  onApproachComplete: () => void;
  lowGraphics?: boolean;
};

import { renderScale, trackFps } from "./quality";

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function reset(widget: CesiumWidget) {
  widget.camera.setView({
    destination: Cartesian3.fromDegrees(52, 22, 15_600_000),
    orientation: { heading: 0, pitch: -Math.PI / 2, roll: 0 },
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
  entryOverview,
  collisionCue,
  followDebris,
  approach,
  onApproachComplete,
  lowGraphics = false,
}: Props) {
  const fpsLabel = useRef<HTMLSpanElement>(null);
  const burstCollection = useRef<PointPrimitiveCollection | null>(null);
  const replayCollection = useRef<PointPrimitiveCollection | null>(null);
  const trailLines = useRef<PolylineCollection | null>(null);
  const entryLines = useRef<PolylineCollection | null>(null);
  const entryLabels = useRef<LabelCollection | null>(null);
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
    const { scene, camera } = instance;
    scene.backgroundColor = Color.fromCssColorString("#060a10");
    if (scene.sun) scene.sun.show = false;
    if (scene.moon) scene.moon.show = false;
    if (scene.globe) {
      scene.globe.baseColor = Color.fromCssColorString("#173953");
      scene.globe.enableLighting = true;
      scene.globe.lightingFadeInDistance = 16_000_000;
      scene.globe.lightingFadeOutDistance = 8_000_000;
      scene.globe.nightFadeInDistance = 16_000_000;
      scene.globe.nightFadeOutDistance = 8_000_000;
    }
    const light = new DirectionalLight({ direction: camera.directionWC });
    scene.light = light;
    const offset = new Cartesian3();
    let clouds: ImageryLayer | undefined;
    const updateLight = () => {
      // Keep a consistent, readable light angle as the camera changes views.
      Cartesian3.multiplyByScalar(camera.rightWC, 0.88, light.direction);
      Cartesian3.multiplyByScalar(camera.upWC, -0.56, offset);
      Cartesian3.add(light.direction, offset, light.direction);
      Cartesian3.add(light.direction, camera.directionWC, light.direction);
      Cartesian3.normalize(light.direction, light.direction);
      if (clouds) {
        const height = camera.positionCartographic.height;
        clouds.alpha = Math.min(
          0.86,
          Math.max(0, (height - 2_500_000) / 5_000_000),
        );
      }
    };
    updateLight();
    const removeLightUpdate = scene.preUpdate.addEventListener(updateLight);
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
    entryLabels.current = instance.scene.primitives.add(new LabelCollection());
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
      maximumLevel: 4,
      hasAlphaChannel: false,
      enablePickFeatures: false,
      credit: new Credit(
        '<a href="https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/base-topography-bathymetry/" target="_blank" rel="noopener noreferrer">NASA Earth Observatory · Blue Marble</a>',
        true,
      ),
    });
    const layer = new ImageryLayer(imagery, {
      saturation: 1.12,
      contrast: 1.13,
      brightness: 1.08,
    });
    const removeImageryError = imagery.errorEvent.addEventListener(() => {
      if (instance.isDestroyed() || !instance.scene.imageryLayers.remove(layer))
        return;
      TileMapServiceImageryProvider.fromUrl(
        "/cesium/Assets/Textures/NaturalEarthII",
        { credit: new Credit("Natural Earth", true) },
      )
        .then((fallback) => {
          if (instance.isDestroyed()) return;
          instance.scene.imageryLayers.add(new ImageryLayer(fallback), 0);
          instance.scene.requestRender();
        })
        .catch(() => {
          if (!instance.isDestroyed())
            setWarning(
              "Local imagery unavailable. Showing the Earth ellipsoid.",
            );
        });
    });
    scene.imageryLayers.add(layer);
    void SingleTileImageryProvider.fromUrl("/earth/archived-clouds.webp", {
      credit: new Credit(
        '<a href="https://svs.gsfc.nasa.gov/4439/" target="_blank" rel="noopener noreferrer">NOAA / NASA SVS · Archived clouds</a>',
        true,
      ),
    })
      .then((provider) => {
        if (instance.isDestroyed()) return;
        clouds = new ImageryLayer(provider);
        scene.imageryLayers.add(clouds);
        updateLight();
        scene.requestRender();
      })
      .catch(() => {
        // The base map remains available if the optional cloud overlay fails.
      });
    scene.requestRender();
    return () => {
      stopFps();
      removeLightUpdate();
      removeError();
      removeImageryError();
      approachPoints.current = null;
      trailLines.current = null;
      entryLines.current = null;
      entryLabels.current = null;
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
    entryLabels.current?.removeAll();
    if (entryCells?.length) {
      const largestCells = [...entryCells]
        .sort((a, b) => b.count - a.count)
        .slice(0, 12);
      for (const cell of largestCells)
        entryLabels.current?.add(entryCellLabel(cell));
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
    if (entryOverview?.length) {
      focusEntryOverview(
        instance.camera,
        entryOverview,
        prefersReducedMotion() ? 0 : 1.5,
      );
    } else if (entryFocus) {
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
  }, [available, entryFocus, entryOverview]);

  const catalogForApproach = useRef(objects);
  catalogForApproach.current = objects;
  const contact = impact?.position;
  useEffect(() => {
    const points = approachPoints.current;
    const instance = widget.current;
    if (!available || !instance || !points || !approach || !contact) return;
    const target = Cartesian3.fromArray(contact);
    const first = Cartesian3.fromArray(approach[0].position);
    const second = Cartesian3.fromArray(approach[1].position);
    const midpoint = Cartesian3.midpoint(first, second, new Cartesian3());
    const shotCenter = Cartesian3.midpoint(midpoint, target, midpoint);
    // Look across the closing paths so one model does not hide the other.
    const localFrame = Transforms.eastNorthUpToFixedFrame(shotCenter);
    const separation = Matrix4.multiplyByPointAsVector(
      Matrix4.inverseTransformation(localFrame, localFrame),
      Cartesian3.subtract(second, first, new Cartesian3()),
      new Cartesian3(),
    );
    const heading = Math.atan2(separation.y, -separation.x);
    const portrait = instance.canvas.clientWidth < instance.canvas.clientHeight;
    focusReplay(
      instance.camera,
      shotCenter,
      0,
      portrait ? 1_950_000 : 2_150_000,
      heading,
    );
    const payloads = new Set(
      catalogForApproach.current
        ?.filter((object) => object.kind === "PAYLOAD")
        .map((object) => object.id),
    );
    const urls = new Map<string, string>();
    for (const { object_id } of approach) {
      if (object_id === "DEMO:ASTEROID")
        urls.set(object_id, "/models/asteroid.glb");
      else if (object_id === "DEMO:004" || payloads.has(object_id))
        urls.set(object_id, "/models/satellite.glb");
    }
    return showApproach(
      instance.scene,
      points,
      approach,
      target,
      urls,
      prefersReducedMotion(),
      () => approachComplete.current(),
    );
  }, [available, approach, contact]);

  useEffect(() => {
    const points = approachPoints.current;
    if (!available || !points || !collisionCue || !contact) return;
    const marker = points.add({
      position: Cartesian3.fromArray(contact),
      color: Color.WHITE,
      outlineColor: Color.ORANGE,
      outlineWidth: 6,
      pixelSize: 22,
    });
    widget.current?.scene.requestRender();
    return () => {
      if (!points.isDestroyed()) points.remove(marker);
    };
  }, [available, collisionCue, contact]);

  useEffect(() => {
    const instance = widget.current;
    if (!instance || !followDebris) return;
    instance.camera.cancelFlight();
    return () => {
      if (!instance.isDestroyed())
        instance.camera.lookAtTransform(Matrix4.IDENTITY);
    };
  }, [followDebris]);

  useEffect(() => {
    const instance = widget.current;
    const fragment = replayPositions?.values().next().value;
    if (!instance || !followDebris || !fragment) return;
    instance.camera.lookAt(
      Cartesian3.fromArray(fragment),
      new HeadingPitchRange(0.35, -0.32, 1_400_000),
    );
    instance.scene.requestRender();
  }, [followDebris, replayPositions]);

  // Keep the collision in a three-quarter view so trails have visible depth.
  useEffect(() => {
    const instance = widget.current;
    if (
      !instance ||
      !available ||
      !impact ||
      !focusToken ||
      approach ||
      followDebris
    )
      return;
    if (lastFocusToken.current === focusToken) return;
    lastFocusToken.current = focusToken;
    focusReplay(
      instance.camera,
      impact.position,
      prefersReducedMotion() ? 0 : 1.4,
    );
    instance.scene.requestRender();
  }, [focusToken, available, impact, approach, followDebris]);

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
