"""Named static instances keep usWeightClass on the 100–900 tier."""
import unittest

from check_static_weight import weight_of_filename
from make_instances import apply_named_weight
import ufoLib2


class StaticWeightTests(unittest.TestCase):
    def test_filename_labels(self):
        self.assertEqual(weight_of_filename("BloxwapSans-ExtraLight.otf"), 200)
        self.assertEqual(weight_of_filename("BloxwapSans-ExtraLightItalic.ttf"), 200)
        self.assertEqual(weight_of_filename("BloxwapSans-Bold.woff2"), 700)
        self.assertEqual(weight_of_filename("BloxwapSans-Italic.ttf"), 400)
        self.assertIsNone(weight_of_filename("BloxwapSans[wght].ttf"))

    def test_apply_named_weight_replaces_interpolated_class(self):
        font = ufoLib2.Font()
        font.info.styleName = "ExtraLight"
        font.info.openTypeOS2WeightClass = 177
        apply_named_weight(font)
        self.assertEqual(font.info.openTypeOS2WeightClass, 200)
        font.info.styleName = "Bold Italic"
        font.info.openTypeOS2WeightClass = 713
        apply_named_weight(font)
        self.assertEqual(font.info.openTypeOS2WeightClass, 700)
        font.info.styleName = "Italic"
        apply_named_weight(font)
        self.assertEqual(font.info.openTypeOS2WeightClass, 400)
