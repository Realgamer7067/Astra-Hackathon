import {
  BoundingSphere,
  Cartesian3,
  Color,
  ColorGeometryInstanceAttribute,
  GeometryInstance,
  HeadingPitchRange,
  Material,
  PerInstanceColorAppearance,
  PolylineCollection,
  Primitive,
  Rectangle,
  RectangleGeometry,
  type Camera,
} from "cesium";
import type { EntryCrossing } from "../features/results/api";
import {
  CELL_DEGREES,
  type EntryCell,
  type FragmentTrack,
} from "../timeline/entryReplay";
import type { Vec3 } from "../timeline/interpolation";

const trail = Color.fromCssColorString("#51d9ff");
const entryColor = Color.fromCssColorString("#ff8e43");
const earthEntryRadius = 6_498_137;

export function entryPosition(entry: EntryCrossing): Cartesian3 {
  const surface = Cartesian3.fromDegrees(
    entry.longitude_deg,
    entry.latitude_deg,
  );
  const normal = Cartesian3.normalize(surface, new Cartesian3());
  return Cartesian3.multiplyByScalar(
    normal,
    earthEntryRadius,
    new Cartesian3(),
  );
}

export function drawTracks(
  collection: PolylineCollection,
  tracks: readonly FragmentTrack[],
) {
  let index = 0;
  for (const track of tracks) {
    const positions = track.points.map((point) => Cartesian3.fromArray(point));
    const tip = positions.at(-1);
    const previous = positions.at(-2);
    if (!tip || !previous) continue;
    const falling =
      Cartesian3.magnitude(tip) < earthEntryRadius + 180_000 &&
      Cartesian3.magnitude(tip) < Cartesian3.magnitude(previous);
    const width = falling ? 5 : 3;
    const color = falling ? entryColor : trail.withAlpha(0.72);
    const glowPower = falling ? 0.22 : 0.18;
    if (index === collection.length) {
      // Cesium owns and destroys each polyline's material independently.
      collection.add({
        positions,
        width,
        material: Material.fromType("PolylineGlow", { color, glowPower }),
      });
    } else {
      const line = collection.get(index);
      line.positions = positions;
      line.width = width;
      line.show = true;
      line.material.uniforms.color = color;
      line.material.uniforms.glowPower = glowPower;
    }
    index += 1;
  }
  for (; index < collection.length; index += 1) {
    collection.get(index).show = false;
  }
}

export function entryHeatmap(cells: readonly EntryCell[]): Primitive {
  const max = Math.max(1, ...cells.map((cell) => cell.count));
  return new Primitive({
    geometryInstances: cells.map(({ west, south, count }) => {
      const strength = Math.sqrt(count / max);
      const color = Color.lerp(
        Color.GOLD,
        Color.ORANGERED,
        strength,
        new Color(),
      ).withAlpha(0.26 + 0.5 * strength);
      return new GeometryInstance({
        geometry: new RectangleGeometry({
          rectangle: Rectangle.fromDegrees(
            west,
            south,
            west + CELL_DEGREES,
            south + CELL_DEGREES,
          ),
          height: 3_000,
          vertexFormat: PerInstanceColorAppearance.FLAT_VERTEX_FORMAT,
        }),
        attributes: { color: ColorGeometryInstanceAttribute.fromColor(color) },
      });
    }),
    appearance: new PerInstanceColorAppearance({
      flat: true,
      translucent: true,
    }),
    asynchronous: false,
    allowPicking: false,
  });
}

export function focusReplay(
  camera: Camera,
  point: Vec3 | Cartesian3,
  duration: number,
) {
  const center = Array.isArray(point) ? Cartesian3.fromArray(point) : point;
  camera.flyToBoundingSphere(new BoundingSphere(center, 210_000), {
    duration,
    offset: new HeadingPitchRange(0.35, -0.32, 1_550_000),
  });
}
