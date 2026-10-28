"""Create a signed, independently versioned Central bundle; never publish it."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
props = dict(line.split('=', 1) for line in (root / 'gradle.properties').read_text().splitlines() if '=' in line)
version = props['aiVersion']
repo = root / 'build/staging-repo'
expected = {'neton-ai'} | {'neton-ai-' + t for t in ('macosarm64', 'macosx64', 'linuxx64', 'linuxarm64', 'mingwx64')}
assert {p.name for p in (repo / 'com/netonstream').iterdir() if p.is_dir()} == expected
manifest = {'version': version, 'frameworkVersion': props['netonVersion'],
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'files': {}}
ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
with zipfile.ZipFile(root / 'build/central-bundle.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
    for artifact in sorted(expected):
        directory = repo / 'com/netonstream' / artifact / version
        assert directory.is_dir(), artifact
        pom = ET.parse(directory / f'{artifact}-{version}.pom').getroot()
        assert pom.findtext('m:version', namespaces=ns) == version
        for dep in pom.findall('.//m:dependency', ns):
            if dep.findtext('m:groupId', namespaces=ns) == 'com.netonstream':
                dependency = dep.findtext('m:artifactId', namespaces=ns)
                wanted = version if dependency in expected else props['netonVersion']
                assert dep.findtext('m:version', namespaces=ns) == wanted
        payloads = [p for p in directory.iterdir() if p.suffix in ('.pom', '.module', '.jar', '.klib')]
        assert any(p.suffix in ('.jar', '.klib') and '-sources' not in p.name for p in payloads)
        for p in payloads:
            signature = Path(str(p) + '.asc')
            assert signature.is_file() and signature.stat().st_size > 0, p
            subprocess.run(['gpg', '--batch', '--verify', str(signature), str(p)], check=True, capture_output=True)
            for f in (p, signature):
                name = f.relative_to(repo).as_posix()
                data = f.read_bytes()
                bundle.writestr(name, data)
                manifest['files'][name] = hashlib.sha256(data).hexdigest()
                for algorithm in ('md5', 'sha1', 'sha256', 'sha512'):
                    bundle.writestr(name + '.' + algorithm, hashlib.new(algorithm, data).hexdigest())
(root / 'build/release-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
