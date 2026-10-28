"""Check independent AI classification and real positive/negative consumers."""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[1]
declaration = re.compile(r'^(?:(?:public|data|sealed|enum|abstract|open|value|inline|suspend|infix|operator|expect|actual|const) )*(?:class|interface|object|fun|val|var|typealias)\b', re.MULTILINE)
for file in (root / 'neton-ai/src').rglob('*.kt'):
    if not any(part.endswith('Main') for part in file.parts):
        continue
    text = file.read_text()
    for match in declaration.finditer(text):
        preceding = text[:match.start()].rstrip().splitlines()
        assert preceding and preceding[-1] == '@neton.ai.ExperimentalNetonAiApi', file
for opt_in in ('true', 'false'):
    result = subprocess.run([str(root / 'gradlew'), '--no-daemon', '-Pai.consumerOptIn=' + opt_in,
                             ':examples:neton-ai-sample:compileKotlinMacosArm64'],
                            cwd=root, capture_output=True, text=True, timeout=1200)
    if opt_in == 'true':
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0 and 'Neton AI is experimental' in result.stdout + result.stderr
print('AI API classification and opt-in consumers passed')
