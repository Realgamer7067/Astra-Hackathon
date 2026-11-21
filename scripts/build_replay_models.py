"""Rebuild ASTRA's original, illustrative glTF models with the Python stdlib."""

import itertools
import json
import math
import random
import struct
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "apps/web/public/models"

type Vec3 = tuple[float, float, float]
type Triangle = tuple[Vec3, Vec3, Vec3]


def normal(a: Vec3, b: Vec3, c: Vec3) -> Vec3:
    ux, uy, uz = (end - start for start, end in zip(a, b, strict=True))
    vx, vy, vz = (end - start for start, end in zip(a, c, strict=True))
    x, y, z = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.hypot(x, y, z)
    return x / length, y / length, z / length


class Mesh:
    def __init__(self) -> None:
        self.groups: dict[str, list[Triangle]] = {}
        self.materials: dict[str, dict[str, object]] = {}

    def material(
        self,
        name: str,
        color: Vec3,
        metallic: float,
        roughness: float,
    ) -> None:
        self.groups[name] = []
        self.materials[name] = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": [*color, 1],
                "metallicFactor": metallic,
                "roughnessFactor": roughness,
            },
        }

    def quad(self, material: str, a: Vec3, b: Vec3, c: Vec3, d: Vec3) -> None:
        self.groups[material].extend([(a, b, c), (a, c, d)])

    def box(self, material: str, center: Vec3, size: Vec3) -> None:
        x, y, z = (value - width / 2 for value, width in zip(center, size, strict=True))
        dx, dy, dz = size
        a, b = (x, y, z), (x + dx, y, z)
        c, d = (x + dx, y + dy, z), (x, y + dy, z)
        e, f = (x, y, z + dz), (x + dx, y, z + dz)
        g, h = (x + dx, y + dy, z + dz), (x, y + dy, z + dz)
        for face in (
            (d, c, b, a),
            (e, f, g, h),
            (a, b, f, e),
            (d, h, g, c),
            (a, e, h, d),
            (b, c, g, f),
        ):
            self.quad(material, *face)

    def write(self, name: str) -> None:
        payload = bytearray()
        views = []
        accessors = []
        primitives = []
        for index, triangles in enumerate(self.groups.values()):
            positions = [point for triangle in triangles for point in triangle]
            normals = [normal(*triangle) for triangle in triangles for _ in range(3)]
            attributes = {}
            for attribute, values in (("POSITION", positions), ("NORMAL", normals)):
                offset = len(payload)
                for value in values:
                    payload.extend(struct.pack("<3f", *value))
                views.append(
                    {
                        "buffer": 0,
                        "byteOffset": offset,
                        "byteLength": len(payload) - offset,
                        "target": 34962,
                    }
                )
                axes = list(zip(*values, strict=True))
                accessors.append(
                    {
                        "bufferView": len(views) - 1,
                        "componentType": 5126,
                        "count": len(values),
                        "type": "VEC3",
                        "min": [min(axis) for axis in axes],
                        "max": [max(axis) for axis in axes],
                    }
                )
                attributes[attribute] = len(accessors) - 1
            primitives.append({"attributes": attributes, "material": index})

        manifest = {
            "asset": {"version": "2.0", "generator": "ASTRA"},
            "scene": 0,
            "scenes": [{"nodes": [0]}],
            "nodes": [{"mesh": 0}],
            "meshes": [{"name": name, "primitives": primitives}],
            "materials": list(self.materials.values()),
            "accessors": accessors,
            "bufferViews": views,
            "buffers": [{"byteLength": len(payload)}],
        }
        header = json.dumps(manifest, separators=(",", ":")).encode()
        header += b" " * (-len(header) % 4)
        chunks = struct.pack("<I4s", len(header), b"JSON") + header
        chunks += struct.pack("<I4s", len(payload), b"BIN\0") + payload
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / f"{name}.glb").write_bytes(
            struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks,
        )


def satellite() -> None:
    mesh = Mesh()
    mesh.material("Aluminum", (0.56, 0.67, 0.77), 0.65, 0.32)
    mesh.material("Gold insulation", (0.66, 0.32, 0.085), 0.45, 0.39)
    mesh.material("Panel frame", (0.05, 0.12, 0.19), 0.32, 0.46)
    mesh.material("Photovoltaic cell", (0.026, 0.19, 0.42), 0.55, 0.28)
    mesh.material("Photovoltaic cell alternate", (0.053, 0.28, 0.56), 0.5, 0.32)

    mesh.box("Gold insulation", (0, 0, 0), (1.25, 0.86, 1.08))
    for y in (-0.44, 0.44):
        mesh.box("Aluminum", (0, y, 0), (1.31, 0.11, 1.13))
    for side in (-1, 1):
        mesh.box("Aluminum", (side * 0.8, 0, 0), (0.42, 0.15, 0.18))
        mesh.box("Panel frame", (side * 2.12, 0, 0), (2.28, 0.14, 1.12))
        for column in range(6):
            for row in range(3):
                cell = (
                    "Photovoltaic cell alternate"
                    if (column + row) % 3 == 0
                    else "Photovoltaic cell"
                )
                mesh.box(
                    cell,
                    (side * (1.2 + column * 0.368), 0.075, (row - 1) * 0.35),
                    (0.338, 0.026, 0.32),
                )
    mesh.box("Aluminum", (0.18, 0.69, -0.14), (0.14, 0.42, 0.14))
    center = (0.18, 0.86, -0.14)
    for i in range(18):
        a = 2 * math.pi * i / 18
        b = 2 * math.pi * (i + 1) / 18
        rim_a = (0.18 + 0.51 * math.cos(a), 1.0, -0.14 + 0.51 * math.sin(a))
        rim_b = (0.18 + 0.51 * math.cos(b), 1.0, -0.14 + 0.51 * math.sin(b))
        mesh.groups["Aluminum"].append((center, rim_b, rim_a))
        mesh.groups["Panel frame"].append((center, rim_a, rim_b))
    mesh.box("Aluminum", (0.18, 1.02, -0.14), (0.075, 0.29, 0.075))
    mesh.write("satellite")


def asteroid() -> None:
    mesh = Mesh()
    for index in range(6):
        shade = 0.14 + index * 0.041
        mesh.material(str(index), (shade * 1.17, shade, shade * 0.87), 0.04, 0.91)

    rng = random.Random(7067)
    slices = 16
    bands = 10
    rings: list[list[Vec3]] = []
    for band in range(1, bands):
        polar = math.pi * band / bands
        ring: list[Vec3] = []
        for segment in range(slices):
            azimuth = 2 * math.pi * (segment + 0.5 * (band % 2)) / slices
            radius = (
                0.95 + 0.11 * math.cos(3 * azimuth) * math.sin(polar) + rng.uniform(-0.09, 0.09)
            )
            ring.append(
                (
                    1.38 * radius * math.sin(polar) * math.cos(azimuth),
                    radius * math.cos(polar),
                    0.89 * radius * math.sin(polar) * math.sin(azimuth),
                )
            )
        rings.append(ring)

    def facet(a: Vec3, b: Vec3, c: Vec3) -> None:
        face = normal(a, b, c)
        if sum(axis * (u + v + w) for axis, u, v, w in zip(face, a, b, c, strict=True)) < 0:
            b, c = c, b
        mesh.groups[str(rng.randrange(6))].append((a, b, c))

    for j in range(slices):
        k = (j + 1) % slices
        facet((0.08, 0.96, 0.03), rings[0][j], rings[0][k])
        facet((-0.07, -0.98, -0.08), rings[-1][k], rings[-1][j])
        for top, bottom in itertools.pairwise(rings):
            facet(top[j], bottom[j], top[k])
            facet(top[k], bottom[j], bottom[k])
    mesh.write("asteroid")


if __name__ == "__main__":
    satellite()
    asteroid()
