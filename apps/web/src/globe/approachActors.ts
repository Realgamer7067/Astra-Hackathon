import {
  Cartesian3,
  Color,
  Matrix3,
  Matrix4,
  Model,
  Transforms,
  type PointPrimitiveCollection,
  type Scene,
} from "cesium";
import type { Vec3 } from "../timeline/interpolation";

export type ApproachBody = { object_id: string; position: Vec3 };

export function showApproach(
  scene: Scene,
  points: PointPrimitiveCollection,
  bodies: readonly ApproachBody[],
  target: Cartesian3,
  modelUrls: ReadonlyMap<string, string>,
  reducedMotion: boolean,
  onComplete: () => void,
) {
  let disposed = false;
  const sizeFactor = Math.min(1, scene.canvas.clientWidth / 600);
  const actors = bodies.map(({ object_id, position }, index) => {
    const start = Cartesian3.fromArray(position);
    const marker = points.add({
      position: start,
      color: index === 0 ? Color.CYAN : Color.ORANGE,
      pixelSize: 14,
      outlineColor: Color.WHITE,
      outlineWidth: 2,
    });
    const actor = {
      start,
      marker,
      model: undefined as Model | undefined,
      modelMatrix: Transforms.eastNorthUpToFixedFrame(start),
      origin: new Cartesian3(),
      rotation: new Matrix3(),
      tilt: Matrix3.fromRotationX(index === 0 ? -0.68 : 0.28),
    };
    const url = modelUrls.get(object_id);
    if (url) {
      void Model.fromGltfAsync({
        url,
        modelMatrix: actor.modelMatrix,
        minimumPixelSize:
          (url.endsWith("asteroid.glb") ? 104 : 152) * sizeFactor,
        enablePick: false,
        lightColor: new Cartesian3(1.65, 1.7, 1.8),
      })
        .then((model) => {
          if (disposed || scene.isDestroyed()) {
            model.destroy();
            return;
          }
          actor.model = scene.primitives.add(model);
          const removeError = model.errorEvent.addEventListener(() => {
            removeError();
            actor.model = undefined;
            scene.primitives.remove(model);
            scene.requestRender();
          });
          scene.requestRender();
        })
        .catch(() => {
          // Keep the marker if the optional asset is unavailable.
        });
    }
    return actor;
  });

  const duration = reducedMotion ? 1000 : 6400;
  const started = performance.now();
  let frame = 0;
  function advance(now: number) {
    const t = Math.min(1, (now - started) / duration);
    for (const [index, actor] of actors.entries()) {
      Cartesian3.lerp(actor.start, target, t, actor.origin);
      actor.marker.position = actor.origin;
      actor.marker.show = !actor.model?.ready;
      if (actor.model) {
        Transforms.eastNorthUpToFixedFrame(
          actor.origin,
          undefined,
          actor.modelMatrix,
        );
        Matrix3.fromRotationZ(
          index === 0 ? -0.65 + 0.3 * t : 0.2 + 1.15 * t,
          actor.rotation,
        );
        Matrix3.multiply(actor.rotation, actor.tilt, actor.rotation);
        Matrix4.multiplyByMatrix3(
          actor.modelMatrix,
          actor.rotation,
          actor.modelMatrix,
        );
        actor.model.modelMatrix = actor.modelMatrix;
      }
    }
    scene.requestRender();
    if (t < 1) frame = requestAnimationFrame(advance);
    else onComplete();
  }

  frame = requestAnimationFrame(advance);
  return () => {
    disposed = true;
    cancelAnimationFrame(frame);
    if (!points.isDestroyed()) {
      for (const { marker, model } of actors) {
        points.remove(marker);
        if (model && !scene.isDestroyed()) scene.primitives.remove(model);
      }
    }
  };
}
