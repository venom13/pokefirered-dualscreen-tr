"""Regression checks for the Android resource collector (no ROM needed)."""
import unittest

from prepare_android import binary_includes


class BinaryIncludesTest(unittest.TestCase):
    def test_single_file(self):
        self.assertEqual(list(binary_includes(
            'const u16 palette[] = INCBIN_U16("graphics/example.gbapal");')),
            ["graphics/example.gbapal"])

    def test_multiple_files_and_lines(self):
        self.assertEqual(list(binary_includes(
            'INCBIN_U32("graphics/first.gbapal",\n'
            '           "graphics/second.gbapal", "graphics/tiles.4bpp.lz");')),
            ["graphics/first.gbapal", "graphics/second.gbapal",
             "graphics/tiles.4bpp.lz"])

    def test_assembly_offset(self):
        self.assertEqual(list(binary_includes(
            '.incbin "sound/sample.bin", 4, 32')),
            ["sound/sample.bin"])

    def test_no_false_plain_strings(self):
        self.assertEqual(list(binary_includes(
            'const char *path = "graphics/not-an-include.png";')), [])


if __name__ == "__main__":
    unittest.main()
