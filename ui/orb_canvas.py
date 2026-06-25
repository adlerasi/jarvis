from __future__ import annotations
import math
import random
import tkinter as tk

STATE_COLORS = {
    "INITIALISING": "#8a8a9a",
    "LISTENING":    "#00ff88",
    "SPEAKING":     "#4488ff",
    "THINKING":     "#ffcc00",
    "ERROR":        "#ff3344",
    "MUTED":        "#cc2255",
    "PAUSED":       "#1e3c37",
}


class Particle3D:
    def __init__(self):
        self.angle = random.uniform(0, math.tau)
        self.elevation = random.uniform(-math.pi/2, math.pi/2)
        self.radius = random.uniform(1.2, 2.8)
        self.speed = random.uniform(-0.02, 0.02)
        self.size = random.uniform(1.0, 3.0)
        self.phase = random.uniform(0, math.tau)
        self.oval_id: int | None = None


class OrbCanvas(tk.Canvas):
    """Optimized OrbCanvas — creates items once, updates in-place.

    Uses coords() and itemconfig() instead of delete+recreate for ~2-3x
    faster frame rendering on the Tkinter canvas.
    """

    def __init__(self, parent, size=320, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg="#020c0c", highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size / 2
        self.cy = size / 2

        self.current_state = "INITIALISING"
        self.target_color = self._hex_to_rgb(STATE_COLORS[self.current_state])
        self.current_color = self.target_color
        self.intensity = 1.0
        self.time = 0.0

        # Perspective
        self.fov = 300
        self.viewer_distance = 4.0

        # Icosahedron
        self._init_icosahedron()

        # Pre-create all canvas items ──
        self._items: dict[str, list[int]] = {}

        # Glow circles (5 layers)
        self._items["glow"] = []
        for _ in range(5):
            self._items["glow"].append(
                self.create_oval(0, 0, 0, 0, outline="#000000", width=1)
            )

        # Icosahedron edges
        self._items["edges"] = []
        for _ in self.edges:
            self._items["edges"].append(
                self.create_line(0, 0, 0, 0, fill="#000000", width=1)
            )

        # Particles (200)
        self.particles = [Particle3D() for _ in range(200)]
        self._items["particles"] = []
        for _ in self.particles:
            self._items["particles"].append(
                self.create_oval(0, 0, 0, 0, fill="#000000", outline="")
            )

        # Torus rings (3 rings × 60 segments)
        self.rings = [
            {"tilt_x": 0.5, "tilt_y": 0.2, "speed": 0.015,
             "radius": 2.6, "segments": 60},
            {"tilt_x": -0.4, "tilt_y": 0.6, "speed": -0.01,
             "radius": 3.0, "segments": 60},
            {"tilt_x": 0.2, "tilt_y": -0.5, "speed": 0.02,
             "radius": 3.4, "segments": 60},
        ]
        self._items["rings"] = []
        for ring in self.rings:
            for _ in range(ring["segments"]):
                self._items["rings"].append(
                    self.create_line(0, 0, 0, 0, fill="#000000", width=1)
                )

        # Start animation loop
        self.after(16, self.animate)

    # ── Color helpers ─────────────────────────────────────────

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(r: float, g: float, b: float) -> str:
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    @staticmethod
    def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
        return (
            c1[0] + (c2[0] - c1[0]) * t,
            c1[1] + (c2[1] - c1[1]) * t,
            c1[2] + (c2[2] - c1[2]) * t,
        )

    # ── Public API (KORUNACAK — thin wrappers for tests/compat) ──

    def set_state(self, state_name: str):
        self.current_state = state_name
        hex_col = STATE_COLORS.get(state_name, STATE_COLORS["LISTENING"])
        self.target_color = self._hex_to_rgb(hex_col)

    def set_base_color(self, hex_color: str):
        self.target_color = self._hex_to_rgb(hex_color)

    def set_intensity(self, intensity: float):
        self.intensity = intensity

    # Public wrappers for tests and external callers
    def hex_to_rgb(self, hex_color: str) -> tuple:
        return OrbCanvas._hex_to_rgb(hex_color)

    def rgb_to_hex(self, r: float, g: float, b: float) -> str:
        return OrbCanvas._rgb_to_hex(r, g, b)

    def lerp_color(self, c1: tuple, c2: tuple, t: float) -> tuple:
        return OrbCanvas._lerp_color(c1, c2, t)

    def project_3d(self, x: float, y: float, z: float):
        return self._project_3d(x, y, z)

    def rotate_y(self, x, y, z, angle):
        return OrbCanvas._rotate_y(x, y, z, angle)

    def rotate_x(self, x, y, z, angle):
        return OrbCanvas._rotate_x(x, y, z, angle)

    def draw_glow_circle(self, x, y, radius, color, alpha_factor):
        # Legacy compatibility — single glow circle draw
        col_hex = self._rgb_to_hex(*color)
        for i in range(5):
            frac = 1.0 - (i / 4.0)
            alpha = alpha_factor * frac * self.intensity
            bg = self._hex_to_rgb("#020c0c")
            r = color[0] * alpha + bg[0] * (1 - alpha)
            g = color[1] * alpha + bg[1] * (1 - alpha)
            b = color[2] * alpha + bg[2] * (1 - alpha)
            r_i = radius * (0.6 + 0.4 * (i / 4.0))
            self.create_oval(x - r_i, y - r_i, x + r_i, y + r_i,
                            outline=self._rgb_to_hex(r, g, b), width=1)

    # ── 3D helpers ────────────────────────────────────────────

    def _project_3d(self, x: float, y: float, z: float):
        scale = self.fov / (self.fov + z * 50 + self.viewer_distance * 50)
        base_scale = self.size / 5.5
        return (self.cx + x * scale * base_scale,
                self.cy + y * scale * base_scale, scale)

    @staticmethod
    def _rotate_y(x, y, z, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        return x * c + z * s, y, -x * s + z * c

    @staticmethod
    def _rotate_x(x, y, z, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        return x, y * c - z * s, y * s + z * c

    def _init_icosahedron(self):
        phi = (1 + math.sqrt(5)) / 2
        self.vertices = [
            (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
            (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
            (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1),
        ]
        length = math.sqrt(1 + phi ** 2)
        self.vertices = [(x / length, y / length, z / length)
                         for x, y, z in self.vertices]
        self.edges = []
        for i in range(12):
            for j in range(i + 1, 12):
                d = sum((self.vertices[i][k] - self.vertices[j][k]) ** 2
                        for k in range(3))
                if abs(d - ((2.0 / length) ** 2)) < 0.1:
                    self.edges.append((i, j))

    # ── Animation (update-only, no delete/recreate) ──────────

    def animate(self):
        self.time += 0.05

        # Smooth color tween
        self.current_color = self._lerp_color(
            self.current_color, self.target_color, 0.08)
        breath = 1.0 + math.sin(self.time * 2) * 0.08 * self.intensity
        rot_time = self.time * 0.5
        bg = self._hex_to_rgb("#020c0c")
        col = self.current_color
        col_hex = self._rgb_to_hex(*col)

        # ── 1. Glow circles (5 layers, update coords + color) ──
        glow_radius = self.size * 0.15 * breath
        for i, item_id in enumerate(self._items["glow"]):
            frac = 1.0 - (i / 4.0)
            alpha = frac * 0.6 * self.intensity
            r = col[0] * alpha + bg[0] * (1 - alpha)
            g = col[1] * alpha + bg[1] * (1 - alpha)
            b = col[2] * alpha + bg[2] * (1 - alpha)
            r_i = glow_radius * (0.6 + 0.4 * (i / 4.0))
            self.coords(item_id,
                        self.cx - r_i, self.cy - r_i,
                        self.cx + r_i, self.cy + r_i)
            self.itemconfig(item_id, outline=self._rgb_to_hex(r, g, b))
            self.tag_lower(item_id)

        # ── 2. Icosahedron edges ──
        proj_verts = []
        for v in self.vertices:
            x, y, z = self._rotate_y(*v, rot_time)
            x, y, z = self._rotate_x(x, y, z, rot_time * 0.7)
            x *= breath * 0.9
            y *= breath * 0.9
            z *= breath * 0.9
            px, py, _ = self._project_3d(x, y, z)
            proj_verts.append((px, py))

        for idx, (i, j) in enumerate(self.edges):
            p1 = proj_verts[i]
            p2 = proj_verts[j]
            item_id = self._items["edges"][idx]
            self.coords(item_id, p1[0], p1[1], p2[0], p2[1])
            self.itemconfig(item_id, fill=col_hex)

        # ── 3. Particles ──
        for idx, p in enumerate(self.particles):
            p.angle += p.speed * self.intensity
            x = p.radius * math.cos(p.angle) * math.cos(p.elevation)
            y = p.radius * math.sin(p.elevation)
            z = p.radius * math.sin(p.angle) * math.cos(p.elevation)
            x, y, z = self._rotate_y(x, y, z, rot_time * 0.2)
            px, py, scale = self._project_3d(x, y, z)
            brightness = max(0, min(1, scale * 0.7 + 0.3))
            alpha = brightness * self.intensity
            r = col[0] * alpha + bg[0] * (1 - alpha)
            g = col[1] * alpha + bg[1] * (1 - alpha)
            b = col[2] * alpha + bg[2] * (1 - alpha)
            psize = p.size * scale * (1.0 + 0.2 * math.sin(self.time + p.phase))
            item_id = self._items["particles"][idx]
            if psize > 0.5:
                self.coords(item_id,
                            px - psize, py - psize,
                            px + psize, py + psize)
                self.itemconfig(item_id, fill=self._rgb_to_hex(r, g, b))
                self.itemconfig(item_id, state="normal")
            else:
                self.itemconfig(item_id, state="hidden")

        # ── 4. Torus rings ──
        ring_idx = 0
        for ring in self.rings:
            ring_angle = self.time * ring["speed"] * (1.0 + self.intensity * 0.5)
            pts = []
            for i in range(ring["segments"]):
                theta = (i / ring["segments"]) * math.tau
                x = ring["radius"] * math.cos(theta)
                z = ring["radius"] * math.sin(theta)
                y = 0.0
                x, y, z = self._rotate_x(x, y, z, ring["tilt_x"])
                x, y, z = self._rotate_y(x, y, z, ring["tilt_y"] + ring_angle)
                px, py, _ = self._project_3d(x, y, z)
                pts.append((px, py, z))

            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[(i + 1) % len(pts)]
                z_avg = (p1[2] + p2[2]) / 2
                brightness = max(0.1, min(1.0, (z_avg + 3) / 6))
                alpha = brightness * 0.7 * self.intensity
                r = col[0] * alpha + bg[0] * (1 - alpha)
                g = col[1] * alpha + bg[1] * (1 - alpha)
                b = col[2] * alpha + bg[2] * (1 - alpha)
                item_id = self._items["rings"][ring_idx]
                self.coords(item_id, p1[0], p1[1], p2[0], p2[1])
                self.itemconfig(item_id, fill=self._rgb_to_hex(r, g, b))
                ring_idx += 1

        self.after(16, self.animate)
