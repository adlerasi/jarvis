from __future__ import annotations

import math
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestParticle3D(unittest.TestCase):
    """Particle3D — Tkinter gerektirmeyen pure data class testi."""

    def test_init_creates_particle(self):
        """Particle3D varsayilan degerlerle olusabilmeli."""
        from ui.orb_canvas import Particle3D
        p = Particle3D()
        self.assertIsNotNone(p)

    def test_angle_range(self):
        """angle 0 ile tau arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.angle, 0)
            self.assertLessEqual(p.angle, math.tau)

    def test_elevation_range(self):
        """elevation -pi/2 ile pi/2 arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.elevation, -math.pi / 2)
            self.assertLessEqual(p.elevation, math.pi / 2)

    def test_radius_range(self):
        """radius 1.2 ile 2.8 arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.radius, 1.2)
            self.assertLessEqual(p.radius, 2.8)

    def test_speed_range(self):
        """speed -0.02 ile 0.02 arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.speed, -0.02)
            self.assertLessEqual(p.speed, 0.02)

    def test_size_range(self):
        """size 1.0 ile 3.0 arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.size, 1.0)
            self.assertLessEqual(p.size, 3.0)

    def test_phase_range(self):
        """phase 0 ile tau arasinda olmali."""
        from ui.orb_canvas import Particle3D
        for _ in range(50):
            p = Particle3D()
            self.assertGreaterEqual(p.phase, 0)
            self.assertLessEqual(p.phase, math.tau)


class TestOrbCanvasPureMath(unittest.TestCase):
    """OrbCanvas'in Tkinter gerektirmeyen pure math fonksiyonlari."""

    def setUp(self):
        # Import edilebilirlik kontrolu (Tkinter olmadan sinifa erisilemez)
        pass

    def test_hex_to_rgb_white(self):
        """hex_to_rgb #ffffff -> (255,255,255)."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.hex_to_rgb(None, "#ffffff")
        self.assertEqual(result, (255, 255, 255))

    def test_hex_to_rgb_black(self):
        """hex_to_rgb #000000 -> (0,0,0)."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.hex_to_rgb(None, "#000000")
        self.assertEqual(result, (0, 0, 0))

    def test_hex_to_rgb_green(self):
        """hex_to_rgb #00ff88 -> (0,255,136)."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.hex_to_rgb(None, "#00ff88")
        self.assertEqual(result, (0, 255, 136))

    def test_hex_to_rgb_strips_hash(self):
        """hex_to_rgb # olmadan da calismali."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.hex_to_rgb(None, "ff0000")
        self.assertEqual(result, (255, 0, 0))

    def test_rgb_to_hex(self):
        """rgb_to_hex (255,0,0) -> #ff0000."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rgb_to_hex(None, 255, 0, 0)
        self.assertEqual(result, "#ff0000")

    def test_rgb_to_hex_green(self):
        """rgb_to_hex (0,255,136) -> #00ff88."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rgb_to_hex(None, 0, 255, 136)
        self.assertEqual(result, "#00ff88")

    def test_rgb_to_hex_zero(self):
        """rgb_to_hex (0,0,0) -> #000000."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rgb_to_hex(None, 0, 0, 0)
        self.assertEqual(result, "#000000")

    def test_rgb_to_hex_floats(self):
        """rgb_to_hex float degerleri int'e cevirmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rgb_to_hex(None, 100.7, 200.3, 50.9)
        self.assertEqual(result, "#64c832")

    def test_lerp_color_half(self):
        """lerp_color t=0.5'te orta noktayi dondurmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.lerp_color(None, (0, 0, 0), (100, 200, 50), 0.5)
        self.assertEqual(result, (50.0, 100.0, 25.0))

    def test_lerp_color_t0(self):
        """lerp_color t=0'da c1'i dondurmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.lerp_color(None, (10, 20, 30), (100, 200, 50), 0.0)
        self.assertEqual(result, (10, 20, 30))

    def test_lerp_color_t1(self):
        """lerp_color t=1'de c2'yi dondurmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.lerp_color(None, (10, 20, 30), (100, 200, 50), 1.0)
        self.assertEqual(result, (100, 200, 50))

    def test_project_3d_center(self):
        """project_3d (0,0,0) merkezde olmali."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        cx, cy, scale = oc.project_3d(0, 0, 0)
        self.assertAlmostEqual(cx, 160.0, places=1)
        self.assertAlmostEqual(cy, 160.0, places=1)
        root.destroy()

    def test_project_3d_positive_z(self):
        """project_3d pozitif z ile scale kuculmeli."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        _, _, scale1 = oc.project_3d(0, 0, 0)
        _, _, scale2 = oc.project_3d(0, 0, 10)
        self.assertLess(scale2, scale1)
        root.destroy()

    def test_rotate_y_zero(self):
        """rotate_y aci=0'da ayni degerleri dondurmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rotate_y(None, 1, 2, 3, 0)
        self.assertEqual(result, (1, 2, 3))

    def test_rotate_y_180(self):
        """rotate_y pi radyanda x,z isaret degistirmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rotate_y(None, 1, 2, 3, math.pi)
        self.assertAlmostEqual(result[0], -1, places=5)
        self.assertEqual(result[1], 2)
        self.assertAlmostEqual(result[2], -3, places=5)

    def test_rotate_y_90(self):
        """rotate_y pi/2 radyanda x->z, z->-x olmali."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rotate_y(None, 1, 2, 3, math.pi / 2)
        self.assertAlmostEqual(result[0], 3, places=5)
        self.assertEqual(result[1], 2)
        self.assertAlmostEqual(result[2], -1, places=5)

    def test_rotate_x_zero(self):
        """rotate_x aci=0'da ayni degerleri dondurmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rotate_x(None, 1, 2, 3, 0)
        self.assertEqual(result, (1, 2, 3))

    def test_rotate_x_180(self):
        """rotate_x pi radyanda y,z isaret degistirmeli."""
        from ui.orb_canvas import OrbCanvas
        result = OrbCanvas.rotate_x(None, 1, 2, 3, math.pi)
        self.assertEqual(result[0], 1)
        self.assertAlmostEqual(result[1], -2, places=5)
        self.assertAlmostEqual(result[2], -3, places=5)

    def test_init_icosahedron(self):
        """init_icosahedron 12 vertex ve 30 edge olusturmali."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        self.assertEqual(len(oc.vertices), 12)
        self.assertEqual(len(oc.edges), 30)
        root.destroy()

    def test_state_colors_seven_states(self):
        """STATE_COLORS 7 durum icermeli."""
        from ui.orb_canvas import STATE_COLORS
        self.assertEqual(len(STATE_COLORS), 7)
        self.assertIn("LISTENING", STATE_COLORS)
        self.assertIn("SPEAKING", STATE_COLORS)
        self.assertIn("THINKING", STATE_COLORS)

    def test_state_colors_format(self):
        """STATE_COLORS degerleri #rrggbb formatinda."""
        from ui.orb_canvas import STATE_COLORS
        for state, color in STATE_COLORS.items():
            self.assertIsInstance(state, str)
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith("#"))
            self.assertEqual(len(color), 7)

    def test_set_state(self):
        """set_state target_color'i guncellemeli."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        oc.set_state("ERROR")
        self.assertEqual(oc.current_state, "ERROR")
        self.assertEqual(oc.target_color, OrbCanvas.hex_to_rgb(None, "#ff3344"))
        root.destroy()

    def test_set_base_color(self):
        """set_base_color target_color'i dogru ayarlamali."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        oc.set_base_color("#ff0000")
        self.assertEqual(oc.target_color, (255, 0, 0))
        root.destroy()

    def test_set_intensity(self):
        """set_intensity intensity'i dogru ayarlamali."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        oc.set_intensity(0.5)
        self.assertEqual(oc.intensity, 0.5)
        root.destroy()

    def test_draw_glow_circle(self):
        """draw_glow_circle Tkinter canvas uzerinde calisabilmeli."""
        from ui.orb_canvas import OrbCanvas
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        oc = OrbCanvas(root, size=320)
        # Hata firlatmamali
        oc.draw_glow_circle(160, 160, 30, (0, 255, 136), 0.5)
        root.destroy()


if __name__ == "__main__":
    unittest.main(verbosity=2)
