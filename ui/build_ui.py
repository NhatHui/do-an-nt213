"""Build the two static entry pages and copy shared assets; standard library only."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ui'

def build():
    template = (SOURCE / 'index.html').read_text(encoding='utf-8')
    for key, label, entry, public in [
        ('php', 'PHP / Apache', ROOT/'php-lab/src/index.php', ROOT/'php-lab/src'),
        ('node', 'Node.js / Express', ROOT/'node-lab/views/index.ejs', ROOT/'node-lab/public'),
    ]:
        text = template.replace('{{PLATFORM}}', label).replace('{{KEY}}', key)
        for platform in ('php', 'node'):
            text = text.replace('{{' + platform.upper() + '_CURRENT}}', 'aria-current="page"' if platform == key else '')
        entry.write_text(text, encoding='utf-8')
        assets = public/'assets'
        assets.mkdir(exist_ok=True)
        for name in ('lab.css', 'lab.js'):
            shutil.copyfile(SOURCE/name, assets/name)
        print(entry)

if __name__ == '__main__':
    build()