"""Consume an exact successful core CI candidate; never publish or use a floating source tree."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify_payload(directory, pin):
    manifest = json.loads((directory / 'evidence.json').read_text())
    assert manifest['passed'] is True and manifest['revision'] == pin['revision']
    assert manifest['version'] == '1.0.0-candidate.' + pin['revision'][:12]
    repository = (directory / 'repository').resolve()
    records = manifest['repository']['files']
    assert records, 'Empty candidate repository'
    seen = set()
    for item in records:
        file = (repository / item['path']).resolve()
        assert file.is_relative_to(repository) and file.is_file() and file not in seen
        seen.add(file)
        assert file.stat().st_size == item['size']
        assert hashlib.sha256(file.read_bytes()).hexdigest() == item['sha256']
    # Core manifests signed payloads, not Maven metadata/checksum/signature sidecars.
    assert seen == {p.resolve() for p in repository.rglob('*')
                    if p.is_file() and p.suffix in {'.pom', '.module', '.jar', '.klib'}}
    return manifest['version'], repository


def main():
    pin = json.loads((ROOT / 'tools/framework-candidate.json').read_text())
    assert re.fullmatch('[0-9a-f]{40}', pin['revision']) and isinstance(pin['run'], int)
    repo = 'netonframework/neton'
    run = json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/actions/runs/{pin["run"]}']))
    assert run['head_sha'] == pin['revision'] and run['conclusion'] == 'success'
    assert run['event'] == 'push' and run['head_branch'] == 'main'
    assert run['path'] == '.github/workflows/backend-ci.yml'
    destination = Path(sys.argv[1]).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    subprocess.run(['gh', 'run', 'download', str(pin['run']), '--repo', repo,
                    '--name', 'candidate-artifacts-' + pin['revision'], '--dir', str(destination)], check=True)
    version, repository = verify_payload(destination, pin)
    # Authenticity comes from the pinned official successful workflow; its manifest records
    # payload hashes after signature verification. No untrusted PR artifact or sibling checkout.
    if os.environ.get('GITHUB_ENV'):
        with open(os.environ['GITHUB_ENV'], 'a') as env:
            env.write(f'ORG_GRADLE_PROJECT_netonVersion={version}\nNETON_CANDIDATE_REPOSITORY={repository}\n')
    print(f'Verified Framework {pin["revision"]}: {version} at {repository}')


if __name__ == '__main__':
    main()
