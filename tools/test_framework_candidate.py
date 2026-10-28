import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from framework_candidate import verify_payload


class CandidateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pin = {'revision': 'a' * 40}
        repository = self.root / 'repository'
        repository.mkdir()
        (repository / 'payload.klib').write_bytes(b'fixture')
        self.manifest = {'passed': True, 'revision': self.pin['revision'],
                         'version': '1.0.0-candidate.' + 'a' * 12,
                         'repository': {'files': [{'path': 'payload.klib', 'size': 7,
                             'sha256': hashlib.sha256(b'fixture').hexdigest()}]}}
        self.save()

    def save(self):
        (self.root / 'evidence.json').write_text(json.dumps(self.manifest))

    def test_valid(self):
        self.assertEqual(verify_payload(self.root, self.pin)[0], self.manifest['version'])

    def test_changed_payload(self):
        (self.root / 'repository/payload.klib').write_bytes(b'tamper!')
        with self.assertRaises(AssertionError): verify_payload(self.root, self.pin)

    def test_wrong_revision(self):
        with self.assertRaises(AssertionError): verify_payload(self.root, {'revision': 'b' * 40})

    def test_unlisted_payload(self):
        (self.root / 'repository/unlisted').write_bytes(b'other')
        with self.assertRaises(AssertionError): verify_payload(self.root, self.pin)

    def test_traversal(self):
        self.manifest['repository']['files'][0]['path'] = '../evidence.json'
        self.save()
        with self.assertRaises(AssertionError): verify_payload(self.root, self.pin)


if __name__ == '__main__': unittest.main()
