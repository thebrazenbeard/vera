from __future__ import annotations
import json, shutil, tempfile, unittest
from pathlib import Path
from scripts.validate_r6a1_release import ROOT,TOKEN,validate

class R6A1ReleaseTests(unittest.TestCase):
    def copy(self):
        td=tempfile.TemporaryDirectory(); root=Path(td.name); (root/'architecture'/'releases').mkdir(parents=True); shutil.copytree(ROOT/'architecture'/'releases'/TOKEN,root/'architecture'/'releases'/TOKEN); return td,root
    def test_valid(self): validate()
    def test_checksum_mutation(self):
        td,root=self.copy()
        try:
            p=root/'architecture'/'releases'/TOKEN/'README.md'; p.write_text(p.read_text()+'x')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'): validate(root)
        finally: td.cleanup()
    def test_missing_file(self):
        td,root=self.copy()
        try:
            (root/'architecture'/'releases'/TOKEN/f'VERA_STATE_{TOKEN}.md').unlink()
            with self.assertRaisesRegex(ValueError,'checksum inventory'): validate(root)
        finally: td.cleanup()
    def test_duplicate_json(self):
        td,root=self.copy()
        try:
            p=root/'architecture'/'releases'/TOKEN/f'VERA_SOURCE_BINDINGS_{TOKEN}.json'; text=p.read_text().replace('{','{"release_id":"duplicate",',1); p.write_text(text)
            import hashlib
            cp=root/'architecture'/'releases'/TOKEN/'CHECKSUMS.sha256'; lines=[]
            for line in cp.read_text().splitlines():
                d,n=line.split(maxsplit=1); lines.append(f"{hashlib.sha256((root/'architecture'/'releases'/TOKEN/n).read_bytes()).hexdigest()}  {n}")
            cp.write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(ValueError,'duplicate JSON key'): validate(root)
        finally: td.cleanup()
    def test_install_authority_promotion(self):
        td,root=self.copy()
        try:
            p=root/'architecture'/'releases'/TOKEN/f'VERA_SOURCE_BINDINGS_{TOKEN}.json'; obj=json.loads(p.read_text()); obj['project_file_replacement_authorized']=True; p.write_text(json.dumps(obj,indent=2)+'\n')
            import hashlib
            cp=root/'architecture'/'releases'/TOKEN/'CHECKSUMS.sha256'; lines=[]
            for line in cp.read_text().splitlines():
                d,n=line.split(maxsplit=1); lines.append(f"{hashlib.sha256((root/'architecture'/'releases'/TOKEN/n).read_bytes()).hexdigest()}  {n}")
            cp.write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(ValueError,'project_file_replacement_authorized'): validate(root)
        finally: td.cleanup()
    def test_authority_provenance_promotion(self):
        td,root=self.copy()
        try:
            p=root/'architecture'/'releases'/TOKEN/f'VERA_SOURCE_BINDINGS_{TOKEN}.json'; obj=json.loads(p.read_text()); obj['authority_provenance']='VERIFIED'; p.write_text(json.dumps(obj,indent=2)+'\n')
            import hashlib
            cp=root/'architecture'/'releases'/TOKEN/'CHECKSUMS.sha256'; lines=[]
            for line in cp.read_text().splitlines():
                d,n=line.split(maxsplit=1); lines.append(f"{hashlib.sha256((root/'architecture'/'releases'/TOKEN/n).read_bytes()).hexdigest()}  {n}")
            cp.write_text('\n'.join(lines)+'\n')
            with self.assertRaisesRegex(ValueError,'authority provenance'): validate(root)
        finally: td.cleanup()
if __name__=='__main__': unittest.main()
