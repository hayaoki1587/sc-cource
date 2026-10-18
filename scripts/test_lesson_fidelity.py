#!/usr/bin/env python3
"""Executable positive and negative tests for the fidelity checker."""
import subprocess
import sys
import tempfile
from pathlib import Path

CHECK = Path(__file__).with_name("check_lesson_fidelity.py").resolve()

def run(root):
    return subprocess.run([sys.executable,str(CHECK),"--root",str(root),"--lessons","99"],capture_output=True,text=True)

with tempfile.TemporaryDirectory() as temp:
    root=Path(temp)
    (root/"lessons").mkdir()
    (root/"sources"/"lessons").mkdir(parents=True)
    original=root/"sources"/"lessons"/"99.md"
    page=root/"lessons"/"99.html"
    # Missing original must fail.
    page.write_text("<main><p>重要な説明です。原文の内容を保ちます。</p></main>",encoding="utf-8")
    assert run(root).returncode != 0,"Missing source was accepted"
    original.write_text("<!-- SOURCE_STATUS: VERIFIED_ORIGINAL -->\n\n重要な説明です。原文の内容を保ちます。",encoding="utf-8")
    assert run(root).returncode == 0,run(root).stdout
    # Dropping a source paragraph must fail.
    page.write_text("<main><p>異なる文章です。内容を変更しました。</p></main>",encoding="utf-8")
    assert run(root).returncode != 0,"Changed source was accepted"
    # Pending review must fail, even with matching text.
    page.write_text("<main><p>重要な説明です。原文の内容を保ちます。</p><!-- SOURCE_FIDELITY_GATE: verbatim_paragraph_comparison=INCOMPLETE --></main>",encoding="utf-8")
    assert run(root).returncode != 0,"Incomplete gate was accepted"
print("Fidelity checker smoke tests PASS")
