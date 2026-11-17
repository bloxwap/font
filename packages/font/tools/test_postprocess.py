import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import postprocess

class AtomicDistributionTests(unittest.TestCase):
    def test_missing_inputs_preserve_previous_distribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / 'fonts/BloxwapSans/variable/good.ttf'
            old.parent.mkdir(parents=True)
            old.write_bytes(b'previous')
            with patch.object(postprocess, 'ROOT', root):
                with self.assertRaises(RuntimeError):
                    postprocess.run(['sans'])
            self.assertEqual(old.read_bytes(), b'previous')

if __name__ == '__main__':
    unittest.main()
