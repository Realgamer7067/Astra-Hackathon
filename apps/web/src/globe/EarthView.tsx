import { useEffect, useRef, useState } from "react";
import {
  Cartesian3,
  Cartographic,
  CesiumWidget,
  Color,
  Credit,
  CreditDisplay,
  ImageryLayer,
  PointPrimitive,
  PointPrimitiveCollection,
  TileMapServiceImageryProvider,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { burstCount, burstParticles } from "./effects";
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
  lowGraphics?: boolean;
};

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
  lowGraphics = false,
}: Props) {
  const burstCollection = useRef<PointPrimitiveCollection | null>(null);
  const replayCollection = useRef<PointPrimitiveCollection | null>(null);
  const replayPoints = useRef<Map<string, PointPrimitive>>(new Map());
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
        showRenderLoopErrors: false,
      });
    } catch {
      setWarning("Earth view needs WebGL 2. The catalog remains available.");
      return;
    }
    widget.current = instance;
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
    reset(instance);
    setAvailable(true);
    const removeError = instance.scene.renderError.addEventListener(() => {
      setAvailable(false);
      setWarning("Earth view stopped rendering. Reload the page to try again.");
    });
    TileMapServiceImageryProvider.fromUrl(
      "/cesium/Assets/Textures/NaturalEarthII",
    )
      .then((imagery) => {
        if (instance.isDestroyed()) return;
        instance.scene.imageryLayers.add(new ImageryLayer(imagery));
        instance.scene.requestRender();
      })
      .catch(() => {
        if (!instance.isDestroyed())
          setWarning("Local imagery unavailable. Showing the Earth ellipsoid.");
      });
    return () => {
      removeError();
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

  // Impact camera: fly (or jump, under reduced motion) above the impact site.
  useEffect(() => {
    const instance = widget.current;
    if (!instance || !impact || !focusToken) return;
    const direction = Cartesian3.normalize(
      Cartesian3.fromArray(impact.position),
      new Cartesian3(),
    );
    instance.camera.flyTo({
      destination: Cartesian3.multiplyByScalar(
        direction,
        6_371_000 + 2_500_000,
        new Cartesian3(),
      ),
      duration: prefersReducedMotion() ? 0 : 1.6,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusToken]);

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
