"""Exercise bundle inventory, version isolation and mandatory signature checks offline."""
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'tools').mkdir()
        self.script = self.root / 'tools/bundle_release.py'
        shutil.copyfile(Path(__file__).with_name('bundle_release.py'), self.script)
        (self.root / 'gradle.properties').write_text('aiVersion=0.1.0-alpha.1\nnetonVersion=1.0.0-beta26\n')
        self.repo = self.root / 'build/staging-repo/com/netonstream'
        self.artifacts = ['neton-ai'] + ['neton-ai-' + t for t in ('macosarm64', 'macosx64', 'linuxx64', 'linuxarm64', 'mingwx64')]
        for artifact in self.artifacts:
            directory = self.repo / artifact / '0.1.0-alpha.1'
            directory.mkdir(parents=True)
            prefix = artifact + '-0.1.0-alpha.1'
            payloads = {
                '.pom': '<project xmlns="http://maven.apache.org/POM/4.0.0"><version>0.1.0-alpha.1</version><dependencies><dependency><groupId>com.netonstream</groupId><artifactId>neton-core</artifactId><version>1.0.0-beta26</version></dependency></dependencies></project>',
                '.jar': 'fixture', '.module': '{}', '-sources.jar': 'source-fixture'
            }
            for suffix, contents in payloads.items():
                (directory / (prefix + suffix)).write_text(contents)
                (directory / (prefix + suffix + '.asc')).write_text('test-signature')

    def execute(self):
        with patch('subprocess.check_output', return_value='a' * 40), patch('subprocess.run') as verify:
            runpy.run_path(str(self.script), run_name='__main__')
            self.assertEqual(verify.call_count, 24)
            for call in verify.call_args_list:
                self.assertEqual(call.args[0][:3], ['gpg', '--batch', '--verify'])
                self.assertTrue(call.kwargs['check'])

    def test_valid_bundle_preserves_independent_version_and_manifest(self):
        self.execute()
        manifest = json.loads((self.root / 'build/release-manifest.json').read_text())
        self.assertEqual(manifest['frameworkVersion'], '1.0.0-beta26')
        self.assertEqual(len(manifest['files']), 48)
        with zipfile.ZipFile(self.root / 'build/central-bundle.zip') as bundle:
            self.assertEqual(len(bundle.namelist()), 240)

    def test_missing_signature_rejected(self):
        next(self.repo.rglob('*.asc')).unlink()
        with self.assertRaises(AssertionError): self.execute()

    def test_framework_version_drift_rejected(self):
        pom = next(self.repo.rglob('*.pom'))
        pom.write_text(pom.read_text().replace('1.0.0-beta26', '0.1.0-alpha.1'))
        with self.assertRaises(AssertionError): self.execute()

    def test_extra_framework_artifact_rejected(self):
        (self.repo / 'neton-core').mkdir()
        with self.assertRaises(AssertionError): self.execute()


if __name__ == '__main__': unittest.main()
