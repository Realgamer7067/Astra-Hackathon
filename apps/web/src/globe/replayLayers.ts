import {
  BoundingSphere,
  Cartesian3,
  Color,
  ColorGeometryInstanceAttribute,
  GeometryInstance,
  EllipseGeometry,
  HeadingPitchRange,
  HorizontalOrigin,
  LabelStyle,
  Material,
  PerInstanceColorAppearance,
  PolylineCollection,
  Primitive,
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

function cellCenter(cell: EntryCell): Cartesian3 {
  return Cartesian3.fromDegrees(
    cell.west + CELL_DEGREES / 2,
    cell.south + CELL_DEGREES / 2,
  );
}

export function entryHeatmap(cells: readonly EntryCell[]): Primitive {
  const max = Math.max(1, ...cells.map((cell) => cell.count));
  return new Primitive({
    geometryInstances: cells.flatMap((cell) => {
      const strength = Math.sqrt(cell.count / max);
      const center = cellCenter(cell);
      const radius = 65_000 + 190_000 * strength;
      return [1, 0.72, 0.42].map((scale, index) => {
        const color = Color.lerp(
          Color.GOLD,
          Color.ORANGERED,
          strength,
          new Color(),
        ).withAlpha(0.14 + 0.12 * index + 0.14 * strength);
        return new GeometryInstance({
          geometry: new EllipseGeometry({
            center,
            semiMajorAxis: radius * scale,
            semiMinorAxis: radius * scale * 0.85,
            height: 3_000 + index * 1_000,
            vertexFormat: PerInstanceColorAppearance.FLAT_VERTEX_FORMAT,
          }),
          attributes: {
            color: ColorGeometryInstanceAttribute.fromColor(color),
          },
        });
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

export function entryCellLabel(cell: EntryCell) {
  return {
    position: Cartesian3.fromDegrees(
      cell.west + CELL_DEGREES / 2,
      cell.south + CELL_DEGREES / 2,
      8_000,
    ),
    text: String(cell.count),
    font: "bold 15px sans-serif",
    style: LabelStyle.FILL_AND_OUTLINE,
    outlineWidth: 2,
    fillColor: Color.WHITE,
    outlineColor: Color.fromCssColorString("#592711"),
    horizontalOrigin: HorizontalOrigin.CENTER,
  };
}

export function focusEntryOverview(
  camera: Camera,
  cells: readonly EntryCell[],
  duration: number,
) {
  if (cells.length === 0) return;
  const peak = cells.reduce((largest, cell) =>
    cell.count > largest.count ? cell : largest,
  );
  const anchor = cellCenter(peak);
  const nearby = cells
    .map(cellCenter)
    .filter((center) => Cartesian3.distance(anchor, center) < 1_000_000);
  const sphere = BoundingSphere.fromPoints(nearby);
  camera.flyToBoundingSphere(sphere, {
    duration,
    offset: new HeadingPitchRange(
      0,
      -Math.PI / 2,
      Math.max(1_650_000, sphere.radius * 4.5),
    ),
  });
}

export function focusReplay(
  camera: Camera,
  point: Vec3 | Cartesian3,
  duration: number,
  range = 1_550_000,
  heading = 0.35,
) {
  const center = Array.isArray(point) ? Cartesian3.fromArray(point) : point;
  camera.flyToBoundingSphere(new BoundingSphere(center, 210_000), {
    duration,
    offset: new HeadingPitchRange(heading, -0.32, range),
  });
}
