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

class OrbCanvas(tk.Canvas):
    def __init__(self, parent, size=320, **kwargs):
        super().__init__(parent, width=size, height=size, bg="#020c0c", highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        
        self.current_state = "INITIALISING"
        self.target_color = self.hex_to_rgb(STATE_COLORS[self.current_state])
        self.current_color = self.target_color
        self.intensity = 1.0
        self.time = 0.0
        
        # 1. Perspective 3D
        self.fov = 300
        self.viewer_distance = 4.0
        
        # 2. Wireframe Icosahedron Core
        self.init_icosahedron()
        
        # 4. Particle System (200 adet)
        self.particles = [Particle3D() for _ in range(200)]
        
        # 5. Torus Rings (3 adet)
        self.rings = [
            {"tilt_x": 0.5, "tilt_y": 0.2, "speed": 0.015, "radius": 2.6, "segments": 60},
            {"tilt_x": -0.4, "tilt_y": 0.6, "speed": -0.01, "radius": 3.0, "segments": 60},
            {"tilt_x": 0.2, "tilt_y": -0.5, "speed": 0.02, "radius": 3.4, "segments": 60},
        ]
        
        # 8. Performance (60fps)
        self.after(16, self.animate)

    # 7. Smooth Color Tweening
    def hex_to_rgb(self, hex_color: str) -> tuple:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def rgb_to_hex(self, r: float, g: float, b: float) -> str:
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        
    def lerp_color(self, c1: tuple, c2: tuple, t: float) -> tuple:
        r = c1[0] + (c2[0] - c1[0]) * t
        g = c1[1] + (c2[1] - c1[1]) * t
        b = c1[2] + (c2[2] - c1[2]) * t
        return (r, g, b)

    # Mevcut API (KORUNACAK)
    def set_state(self, state_name: str):
        self.current_state = state_name
        hex_col = STATE_COLORS.get(state_name, STATE_COLORS.get("LISTENING"))
        self.target_color = self.hex_to_rgb(hex_col)
        
    def set_base_color(self, hex_color: str):
        self.target_color = self.hex_to_rgb(hex_color)
        
    def set_intensity(self, intensity: float):
        self.intensity = intensity

    # 1. Perspective 3D Projection
    def project_3d(self, x: float, y: float, z: float):
        scale = self.fov / (self.fov + z * 50 + self.viewer_distance * 50)
        base_scale = self.size / 5.5
        return self.cx + x * scale * base_scale, self.cy + y * scale * base_scale, scale

    def rotate_y(self, x, y, z, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        return x * c + z * s, y, -x * s + z * c

    def rotate_x(self, x, y, z, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        return x, y * c - z * s, y * s + z * c

    def init_icosahedron(self):
        phi = (1 + math.sqrt(5)) / 2
        self.vertices = [
            (-1, phi, 0), (1, phi, 0), (-1, -phi, 0), (1, -phi, 0),
            (0, -1, phi), (0, 1, phi), (0, -1, -phi), (0, 1, -phi),
            (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1)
        ]
        length = math.sqrt(1 + phi**2)
        self.vertices = [(x/length, y/length, z/length) for x, y, z in self.vertices]
        
        self.edges = []
        for i in range(12):
            for j in range(i+1, 12):
                d = sum((self.vertices[i][k] - self.vertices[j][k])**2 for k in range(3))
                if abs(d - ((2.0/length)**2)) < 0.1:
                    self.edges.append((i, j))

    # 6. Glow Efektleri
    def draw_glow_circle(self, x, y, radius, color, alpha_factor):
        bg = self.hex_to_rgb("#020c0c")
        for i in range(5):
            frac = 1.0 - (i / 4.0)
            alpha = alpha_factor * frac * self.intensity
            r = color[0] * alpha + bg[0] * (1 - alpha)
            g = color[1] * alpha + bg[1] * (1 - alpha)
            b = color[2] * alpha + bg[2] * (1 - alpha)
            col_hex = self.rgb_to_hex(r, g, b)
            r_i = radius * (0.6 + 0.4 * (i/4.0))
            self.create_oval(x - r_i, y - r_i, x + r_i, y + r_i, outline=col_hex, width=1)

    def animate(self):
        self.time += 0.05
        
        # 7. Smooth Color Tweening
        self.current_color = self.lerp_color(self.current_color, self.target_color, 0.08)
        
        self.delete("all")
        
        # Nefes Alma scale
        breath = 1.0 + math.sin(self.time * 2) * 0.08 * self.intensity
        
        # 3. Inner Glow Sphere
        self.draw_glow_circle(self.cx, self.cy, self.size * 0.15 * breath, self.current_color, 0.6)
        
        rot_time = self.time * 0.5
        
        # 2. Wireframe Icosahedron Core
        proj_verts = []
        for v in self.vertices:
            x, y, z = self.rotate_y(*v, rot_time)
            x, y, z = self.rotate_x(x, y, z, rot_time * 0.7)
            x *= breath * 0.9
            y *= breath * 0.9
            z *= breath * 0.9
            px, py, scale = self.project_3d(x, y, z)
            proj_verts.append((px, py))
            
        core_color = self.rgb_to_hex(*self.current_color)
        for i, j in self.edges:
            p1 = proj_verts[i]
            p2 = proj_verts[j]
            self.create_line(p1[0], p1[1], p2[0], p2[1], fill=core_color, width=1)
            
        # 4. Particle System
        bg_color = self.hex_to_rgb("#020c0c")
        for p in self.particles:
            p.angle += p.speed * self.intensity
            x = p.radius * math.cos(p.angle) * math.cos(p.elevation)
            y = p.radius * math.sin(p.elevation)
            z = p.radius * math.sin(p.angle) * math.cos(p.elevation)
            
            x, y, z = self.rotate_y(x, y, z, rot_time * 0.2)
            px, py, scale = self.project_3d(x, y, z)
            
            # Additive Blending Simülasyonu
            brightness = max(0, min(1, scale * 0.7 + 0.3))
            alpha = brightness * self.intensity
            r = self.current_color[0] * alpha + bg_color[0] * (1 - alpha)
            g = self.current_color[1] * alpha + bg_color[1] * (1 - alpha)
            b = self.current_color[2] * alpha + bg_color[2] * (1 - alpha)
            p_color = self.rgb_to_hex(r, g, b)
            
            psize = p.size * scale * (1.0 + 0.2 * math.sin(self.time + p.phase))
            if psize > 0.5:
                self.create_oval(px - psize, py - psize, px + psize, py + psize, fill=p_color, outline="")
                
        # 5. Torus Rings
        for ring in self.rings:
            ring_angle = self.time * ring["speed"] * (1.0 + self.intensity * 0.5)
            pts = []
            for i in range(ring["segments"]):
                theta = (i / ring["segments"]) * math.tau
                x = ring["radius"] * math.cos(theta)
                z = ring["radius"] * math.sin(theta)
                y = 0
                
                x, y, z = self.rotate_x(x, y, z, ring["tilt_x"])
                x, y, z = self.rotate_y(x, y, z, ring["tilt_y"] + ring_angle)
                
                px, py, scale = self.project_3d(x, y, z)
                pts.append((px, py, z))
                
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[(i+1)%len(pts)]
                
                z_avg = (p1[2] + p2[2]) / 2
                brightness = max(0.1, min(1.0, (z_avg + 3) / 6))
                alpha = brightness * 0.7 * self.intensity
                
                r = self.current_color[0] * alpha + bg_color[0] * (1 - alpha)
                g = self.current_color[1] * alpha + bg_color[1] * (1 - alpha)
                b = self.current_color[2] * alpha + bg_color[2] * (1 - alpha)
                ring_col = self.rgb_to_hex(r, g, b)
                
                self.create_line(p1[0], p1[1], p2[0], p2[1], fill=ring_col, width=1)
                
        self.after(16, self.animate)
