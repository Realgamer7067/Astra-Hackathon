import { useEffect, useRef, useState } from "react";
import {
  Cartesian3,
  Cartographic,
  CesiumWidget,
  Color,
  Credit,
  CreditDisplay,
  ImageryLayer,
  PointPrimitiveCollection,
  TileMapServiceImageryProvider,
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import {
  type CartesianState,
  type CatalogObject,
  kindColors,
} from "../app/demo";

type Props = {
  states?: CartesianState[];
  objects?: CatalogObject[];
  selectedId: string | null;
};

function reset(widget: CesiumWidget) {
  widget.camera.setView({
    destination: Cartesian3.fromDegrees(65, 23, 18_000_000),
  });
  widget.scene.requestRender();
}

export default function EarthView({ states, objects, selectedId }: Props) {
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
