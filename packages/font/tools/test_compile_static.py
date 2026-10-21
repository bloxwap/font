"""Check the paired in-memory path against the original CLI (SIL OFL-1.1)."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fontTools.designspaceLib import (AxisDescriptor, DesignSpaceDocument,
                                      DiscreteAxisDescriptor, InstanceDescriptor,
                                      SourceDescriptor)
from fontTools.designspaceLib.split import splitInterpolable
from fontTools.ttLib import TTFont
from fontmake.instantiator import Instantiator
from ufo2ft import featureCompiler
import ufoLib2

from compile_static import compile_instance
from make_instances import _interpolator, instance_descriptors

TOOLS = Path(__file__).resolve().parent


def normalized_tables(path):
    with TTFont(path) as font:
        tables = {tag: font.reader[tag] for tag in font.reader.keys()}
        head = tables["head"]
        tables["head"] = head[:8] + bytes(4) + head[12:20] + bytes(16) + head[36:]
        return tables


def fixture(root):
    doc = DesignSpaceDocument()
    doc.addAxis(AxisDescriptor(name="Weight", tag="wght", minimum=100, default=100, maximum=900))
    doc.addAxis(DiscreteAxisDescriptor(name="Italic", tag="ital", values=[0, 1], default=0))
    for italic in (0, 1):
        for weight in (100, 900):
            font = ufoLib2.Font()
            font.info.familyName = "Pool Test"
            font.info.styleName = f"Master{weight}{italic}"
            font.info.unitsPerEm = 1000
            font.info.ascender, font.info.descender = 800, -200
            font.info.openTypeNameLicense = "SIL Open Font License, Version 1.1"
            font.info.openTypeNameLicenseURL = "https://openfontlicense.org"
            font.info.copyright = "Clean-room build regression fixture. SIL OFL-1.1."
            for name in (".notdef", "A", "A.alt", "acute", "Acomp"):
                glyph = font.newGlyph(name)
                glyph.width = 600
                if name == "Acomp":
                    glyph.getPen().addComponent("A", (1, 0, 0, 1, 20, 0))
                else:
                    pen = glyph.getPen()
                    for dx in (0, 80):
                        pen.moveTo((dx + italic, 0))
                        pen.lineTo((dx + 100 + weight / 10, 0))
                        pen.curveTo((dx + 220, 100), (dx + 220, 500), (dx + 100, 600))
                        pen.lineTo((dx, 600)); pen.closePath()
            font["A"].unicode = 65
            font["acute"].unicode = 0x301
            font.lib["public.glyphOrder"] = list(font.keys())
            font.features.text = '''languagesystem DFLT dflt;
feature liga { sub A A by A.alt; } liga;
feature ss01 { featureNames { name "Alternate"; }; sub A by A.alt; } ss01;
feature kern { pos A A -30; } kern;
'''
            if italic:
                font.features.text += "table OS/2 { TypoAscender 777; } OS/2;\n"
            path = root / f"master-{weight}-{italic}.ufo"
            font.save(path)
            doc.addSource(SourceDescriptor(path=str(path), name=path.stem,
                                           familyName="Pool Test", location={"Weight": weight, "Italic": italic}))
        for weight in (400, 700):
            doc.addInstance(InstanceDescriptor(familyName="Pool Test", styleName=f"Instance{weight}{italic}",
                                              filename=f"instances/test-{weight}-{italic}.ufo",
                                              location={"Weight": weight, "Italic": italic}))
    ds = root / "test.designspace"
    doc.write(ds)
    return ds


class StaticCompileTests(unittest.TestCase):
    def test_both_formats_match_cli_with_discrete_axes_and_feature_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ds = fixture(root)
            self.addCleanup(_interpolator.cache_clear)
            expected = root / "expected"
            actual = root / "actual"
            expected.mkdir(); actual.mkdir()
            env = dict(os.environ, PYTHONPATH=str(TOOLS))
            # Reference is the original serial interpolation and separate CLI
            # invocations, independent of the optimized helper and shared state.
            doc = DesignSpaceDocument.fromfile(ds)
            for _loc, sub in splitInterpolable(doc):
                sub.loadSourceFonts(ufoLib2.Font.open)
                inst = Instantiator.from_designspace(sub, round_geometry=True)
                for desc in sub.instances:
                    ufo = expected / Path(desc.filename).name
                    inst.generate_instance(desc).save(ufo)
                    for fmt in ("otf", "ttf"):
                        filt = "bwfont.ufo2ft_filters::RobustRemoveOverlapsFilter"
                        if fmt == "ttf":
                            filt += "(pre=True)"
                        subprocess.run([sys.executable, "-m", "fontmake", "-u", str(ufo),
                                        "-o", fmt, "--output-dir", str(expected / fmt),
                                        "--keep-overlaps", "--filter", filt],
                                       env=env, check=True, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE)
            with patch.object(featureCompiler, "addOpenTypeFeaturesFromString",
                              wraps=featureCompiler.addOpenTypeFeaturesFromString) as build:
                for group, index, filename in instance_descriptors(ds):
                    compile_instance(str(ds), group, index, filename, str(actual))
                # Upright instances share layout compilation. Custom table
                # statements in the italic sources take the normal path twice.
                self.assertEqual(build.call_count, 6)
            for fmt in ("otf", "ttf"):
                for before in (expected / fmt).glob(f"*.{fmt}"):
                    self.assertEqual(normalized_tables(before),
                                     normalized_tables(actual / fmt / before.name), before.name)


if __name__ == "__main__":
    unittest.main()
