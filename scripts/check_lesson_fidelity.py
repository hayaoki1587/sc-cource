#!/usr/bin/env python3
"""Fail-closed source fidelity audit for SC lesson HTML.

Original source is required at sources/lessons/NN.md. The file must contain the
original lecture (excluding quiz/grading) with original text/code, not a summary.
Every substantive source paragraph, code block, and SVG must survive in order.
This check deliberately does not certify graphical visual equivalence.
"""
import argparse
import html
from html.parser import HTMLParser
from pathlib import Path
import re
import sys

class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out=[]
        self.skip=0
        self.skip_stack=[]
        self.svg=0
        self.svg_count=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if self.skip:
            self.skip+=1
            return
        if tag in ('style','script','nav','header','footer') or attrs.get('id','').startswith('source-recovery-'):
            self.skip=1
            return
        if tag=='svg':
            self.svg+=1
            self.svg_count+=1
        if tag in ('p','li','h1','h2','h3','td','th','tr','pre','section','br','div'):
            self.out.append('\n')
    def handle_endtag(self,tag):
        if self.skip:
            self.skip-=1
            return
        if tag=='svg' and self.svg: self.svg-=1
        if tag in ('p','li','h1','h2','h3','td','th','tr','pre','section','div'):
            self.out.append('\n')
    def handle_data(self,data):
        if not self.skip and not self.svg:self.out.append(data)

def normalize(s):
    s=html.unescape(s)
    return re.sub(r'\s+','',s).replace('＜','<').replace('＞','>')

def chunks(source):
    source=re.sub(r'<!--\\s*SOURCE_STATUS:\\s*VERIFIED_ORIGINAL\\s*-->', '', source)
    # Preserve fenced code as a single unit; paragraphs otherwise.
    parts=re.split(r'(```[\s\S]*?```)',source)
    out=[]
    for part in parts:
        if part.startswith('```'):
            out.append(re.sub(r'^\`\`\`[^\n]*\n|\n\`\`\`$', '', part))
        else:
            for p in re.split(r'\n\s*\n',part):
                p=re.sub(r'(?m)^\s*#{1,6}\s*','',p)
                p=re.sub(r'(?m)^\s*[-*]\s+','',p)
                p=re.sub(r'(?m)^\s*\d+\.\s+','',p)
                p=p.replace('**','').replace('`','')
                if normalize(p):out.append(p)
    return out

def audit(n,root):
    src=root/'sources'/'lessons'/f'{n}.md'
    page=root/'lessons'/f'{n}.html'
    if not src.is_file():return [f'MISSING ORIGINAL: {src}']
    if not page.is_file():return [f'MISSING PAGE: {page}']
    source=src.read_text(encoding='utf-8')
    raw=page.read_text(encoding='utf-8')
    if 'SOURCE_STATUS: VERIFIED_ORIGINAL' not in source:
        return [f'UNVERIFIED ORIGINAL: {src} (requires explicit provenance marker)']
    if 'SOURCE_FIDELITY_GATE' in raw and 'verbatim_paragraph_comparison=INCOMPLETE' in raw:
        return [f'INCOMPLETE FIDELITY GATE: {page}']
    parser=Extract();parser.feed(raw)
    hay=normalize(''.join(parser.out))
    problems=[]
    cursor=0
    for idx,part in enumerate(chunks(source),1):
        needle=normalize(part)
        if len(needle)<12:continue
        pos=hay.find(needle,cursor)
        if pos<0:
            problems.append(f'OMITTED/REORDERED source chunk {idx}: {needle[:85]}')
            if len(problems)>=20:break
        else:cursor=pos+len(needle)
    expected_svg=len(re.findall(r'<svg\b',source,re.I))
    actual_svg=len(re.findall(r'<svg\b',raw,re.I))
    if actual_svg<expected_svg:
        problems.append(f'SVG LOSS: original {expected_svg}, HTML {actual_svg}')
    # A source containing diagrams represented as SVG requires matching markup
    for svg in re.findall(r'<svg\b[\s\S]*?</svg>',source,re.I):
        if normalize(svg) not in normalize(raw):
            problems.append('SVG markup differs from source')
    return problems

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='.')
    p.add_argument('--lessons',nargs='+',default=['25','26','27'])
    args=p.parse_args()
    failures=0
    for n in args.lessons:
        issues=audit(n,Path(args.root))
        if issues:
            failures+=1
            print(f'FAIL lesson {n}:')
            for issue in issues:print('  -',issue)
        else:print(f'PASS lesson {n}')
    print(f'Fidelity gate: {len(args.lessons)-failures}/{len(args.lessons)} PASS')
    return 1 if failures else 0
if __name__=='__main__':sys.exit(main())
