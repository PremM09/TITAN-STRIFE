"""Rebuild the browser package while keeping the approved mobile loader."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as temporary:
    project = Path(temporary) / 'titan-strife-web'
    project.mkdir()
    for name in ('main.py', 'combat.py', 'sprites.py', 'arena.py', 'effects.py'):
        shutil.copy2(ROOT / name, project / name)
    shutil.copytree(ROOT / 'assets', project / 'assets')
    subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--archive',
                    '--title', 'Titan Strife', str(project)], check=True)
    built = project / 'build' / 'web'
    if not (built / 'titan-strife-web.apk').exists():
        raise RuntimeError('Pygbag did not produce the expected browser bundle.')
    shutil.copy2(ROOT / 'web' / 'index.html', built / 'index.html')
    destination = ROOT / 'build'
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination / 'Titan-Strife-Web.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(built.iterdir()):
            if path.is_file():
                archive.write(path, path.name)
    print(destination / 'Titan-Strife-Web.zip')
