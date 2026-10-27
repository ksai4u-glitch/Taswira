"""Tests for history/geo/make_plates.py, on a small made-up model. Run from the repository folder:

    python -m unittest discover -s tests
"""

import contextlib
import io
import math
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "history", "geo"))
import make_plates as mp  # noqa: E402

# Plate 701 turns 30° about the pole at 0° N 0° E over 100 million years. Plate 201 is
# fixed to 701 and turns a further 10° about the North Pole. Plate 702 follows 701 until
# 50 million years ago, then plate 0 (a crossover). Plate 999 lines are comments.
ROT = """\
701   0.0  90.0   0.0   0.0  000 ! Africa
701 100.0   0.0   0.0  30.0  000 ! Africa
201   0.0  90.0   0.0   0.0  701 ! South America
201 100.0  90.0   0.0  10.0  701 ! South America
702   0.0  90.0   0.0   0.0  701 ! Madagascar
702  50.0   0.0   0.0   0.0  701 ! Madagascar
702  50.0   0.0   0.0  15.0  000 ! crossover
702 100.0   0.0   0.0  30.0  000 ! crossover
999 100.0  10.0  10.0  10.0  999 ! a comment line
"""

GPML = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpml:FeatureCollection xmlns:gpml="http://www.gplates.org/gplates" xmlns:gml="http://www.opengis.net/gml">
 <gml:featureMember>
  <gpml:UnclassifiedFeature>
   <gml:name>Box</gml:name>
   <gpml:reconstructionPlateId><gpml:ConstantValue><gpml:value>701</gpml:value></gpml:ConstantValue></gpml:reconstructionPlateId>
   <gml:validTime><gml:TimePeriod>
    <gml:begin><gml:TimeInstant><gml:timePosition gml:frame="http://gplates.org/TRS/flat">http://gplates.org/times/distantPast</gml:timePosition></gml:TimeInstant></gml:begin>
    <gml:end><gml:TimeInstant><gml:timePosition gml:frame="http://gplates.org/TRS/flat">http://gplates.org/times/distantFuture</gml:timePosition></gml:TimeInstant></gml:end>
   </gml:TimePeriod></gml:validTime>
   <gpml:outlineOf><gpml:ConstantValue><gpml:value><gml:Polygon><gml:exterior><gml:LinearRing>
    <gml:posList gml:dimension="2">0 0 0 5 0 10 10 10 10 0 0 0</gml:posList>
   </gml:LinearRing></gml:exterior></gml:Polygon></gpml:value></gpml:ConstantValue></gpml:outlineOf>
  </gpml:UnclassifiedFeature>
 </gml:featureMember>
 <gml:featureMember>
  <gpml:UnclassifiedFeature>
   <gml:name>Speck</gml:name>
   <gpml:reconstructionPlateId><gpml:ConstantValue><gpml:value>201</gpml:value></gpml:ConstantValue></gpml:reconstructionPlateId>
   <gpml:outlineOf><gpml:ConstantValue><gpml:value><gml:Polygon><gml:exterior><gml:LinearRing>
    <gml:posList gml:dimension="2">0 0 0 0.1 0.1 0.1 0.1 0 0 0</gml:posList>
   </gml:LinearRing></gml:exterior></gml:Polygon></gpml:value></gpml:ConstantValue></gpml:outlineOf>
  </gpml:UnclassifiedFeature>
 </gml:featureMember>
</gpml:FeatureCollection>
"""


def moved(q, lat, lon):
    return mp.to_latlon(mp.rotate(q, mp.to_xyz(lat, lon)))


class PlateModelTests(unittest.TestCase):
    def setUp(self):
        self.plates = mp.read_rotations(ROT)

    def assertNear(self, got, want, places=6):
        for g, w in zip(got, want):
            self.assertAlmostEqual(g, w, places=places)

    def test_comment_lines_are_skipped_and_sequences_split(self):
        self.assertNotIn(999, self.plates)
        self.assertEqual([fixed for fixed, _ in self.plates[702]], [701, 0])

    def test_rotation_is_blended_between_entries(self):
        # Halfway in time is halfway round: 15° about the pole at 0° N 0° E carries 0° N 90° E up to 15° N
        q = mp.total(self.plates, 701, 50.0)
        self.assertNear(moved(q, 0, 90), (15, 90))
        self.assertNear(mp.total(self.plates, 701, 0.0), (1, 0, 0, 0))

    def test_rotations_chain_through_the_fixed_plate(self):
        # 201 at 100 Ma: first 10° about the North Pole (relative to 701), then 701's 30° about 0° N 0° E
        q = mp.total(self.plates, 201, 100.0)
        step = moved(mp.quat_from_pole(90, 0, 10), 0, 90)
        self.assertNear(step, (0, 100))
        self.assertNear(moved(q, 0, 90), moved(mp.quat_from_pole(0, 0, 30), *step))

    def test_crossover_uses_the_sequence_that_covers_the_time(self):
        self.assertNear(mp.total(self.plates, 702, 75.0), mp.quat_from_pole(0, 0, 22.5))
        self.assertNear(mp.total(self.plates, 702, 25.0), mp.total(self.plates, 701, 25.0))

    def test_unknown_plate_or_time_gives_none(self):
        self.assertIsNone(mp.total(self.plates, 123, 10.0))
        self.assertIsNone(mp.total(self.plates, 701, 150.0))

    def test_outlines_are_read_with_latitude_first(self):
        shapes = mp.read_shapes(GPML)
        self.assertEqual([s["plate"] for s in shapes], [701, 201])
        box = shapes[0]
        self.assertEqual(box["from"], math.inf)
        self.assertEqual(box["to"], 0.0)
        self.assertEqual(box["rings"][0][3], (10.0, 10.0))
        self.assertEqual(shapes[1]["from"], math.inf)          # no valid time: always there

    def test_area_and_simplify(self):
        box = [(0, 0), (0, 10), (10, 10), (10, 0), (0, 0)]
        self.assertAlmostEqual(mp.ring_area(box) / 1.23e6, 1, places=1)   # about 1.23 million km²
        # The point at 0° N 5° E lies on the equator between its neighbours, so it goes
        self.assertEqual(mp.simplify([(0, 0), (0, 5), (0, 10), (10, 10), (0, 0)], 0.25),
                         [(0, 0), (0, 10), (10, 10), (0, 0)])

    def test_make_keeps_big_outlines_and_their_plates(self):
        data = mp.make(ROT, GPML, oldest=100, step=50)
        self.assertEqual(data["times"], [0, 50, 100])
        self.assertEqual(len(data["shapes"]), 1)               # the speck is too small
        self.assertEqual(data["shapes"][0]["plate"], 701)
        self.assertEqual(data["shapes"][0]["ring"][0], [0, 0])
        self.assertEqual(list(data["rotations"]), ["701"])
        self.assertEqual(data["rotations"]["701"][0], [10000, 0, 0, 0])
        self.assertEqual(data["rotations"]["701"][2][1], round(10000 * math.sin(math.radians(15))))

    def test_the_benue_trough_is_drawn_at_all_times(self):
        # The model gives the trough's outlines the years 0 to 0; they are kept for every time
        gpml = GPML.replace(b"<gml:name>Box</gml:name>", b"<gml:name>Benue Trough (Central Africa Plate)</gml:name>")
        gpml = gpml.replace(b"http://gplates.org/times/distantPast", b"0").replace(b"http://gplates.org/times/distantFuture", b"0")
        self.assertEqual(mp.read_shapes(gpml)[0]["from"], 0.0)
        self.assertEqual(mp.make(ROT, gpml, oldest=100, step=50)["shapes"][0]["from"], 10 ** 4)

    def test_a_plate_that_moves_with_another_names_it(self):
        # 703 is fixed to 701 and never moves against it, so it has the same rotations
        rot = ROT + "703 0.0 90.0 0.0 0.0 701 ! Fixed\n703 100.0 90.0 0.0 0.0 701 ! Fixed\n"
        gpml = GPML.replace(b"<gpml:value>201</gpml:value>", b"<gpml:value>703</gpml:value>").replace(
            b"0 0 0 0.1 0.1 0.1 0.1 0 0 0", b"20 0 20 10 30 10 30 0 20 0")
        data = mp.make(rot, gpml, oldest=100, step=50)
        self.assertEqual(data["rotations"]["703"], "701")

    def test_model_files_are_found_by_name_inside_the_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "model.zip")
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("Rotations/1000_0_rotfile_Merdith_etal.rot", ROT)
                z.writestr("Continents/shapes_continents.gpml", GPML)
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rot, cont = mp.read_model(path)
        self.assertEqual(rot, ROT)
        self.assertEqual(cont, GPML)
        self.assertIn("md5", out.getvalue())            # not the Zenodo zip, so it says so


if __name__ == "__main__":
    unittest.main()
