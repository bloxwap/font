#!/usr/bin/env python3
# SPDX-License-Identifier: OFL-1.1
"""Local font benchmarks. Driver uses stdlib; font operations use the repo venv."""
import argparse
import datetime as dt
import gzip
import html.parser
import importlib
import io
import json
import os
from pathlib import Path
import platform
import pstats
import re
import resource
import shutil
import statistics
import subprocess
import sys
import time
from urllib.parse import quote, unquote, urlsplit

BASE = Path(__file__).resolve().parents[1]
RESULTS = Path(__file__).resolve().parent / 'results'
LATIN = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD'


def capture(cmd, cwd=None):
    p = subprocess.run(list(map(str, cmd)), cwd=cwd, env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(f'{cmd}: {p.stderr[-4000:]}')
    return p.stdout.strip()


def usage():
    a, b = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
    return a, b


def timed(stage, fn, **tags):
    before = usage()
    start = time.perf_counter()
    row = dict(stage=stage, **tags)
    try:
        result = fn()
        row['status'] = 'ok'
        return result
    except Exception as e:
        row.update(status='error', error=str(e))
        raise
    finally:
        after = usage()
        row.update(wall_seconds=time.perf_counter() - start,
                   cpu_seconds=sum((y.ru_utime+y.ru_stime)-(x.ru_utime+x.ru_stime) for x,y in zip(before,after)),
                   children_cpu_seconds=(after[1].ru_utime+after[1].ru_stime)-(before[1].ru_utime+before[1].ru_stime),
                   children_peak_rss_kib=after[1].ru_maxrss, self_peak_rss_kib=after[0].ru_maxrss)
        DATA['measurements'].append(row)
        print(f"{stage}: {row['wall_seconds']:.3f}s ({row['status']})", flush=True)


def command(cmd, log, cwd=None):
    with (RESULTS / f'{STAMP}-{log}.log').open('w') as f:
        subprocess.run(list(map(str, cmd)), cwd=cwd or FONT, env=ENV, stdout=f, stderr=subprocess.STDOUT, check=True)


def modules():
    sys.path.insert(0, str(FONT / 'tools'))
    return importlib.import_module('postprocess'), importlib.import_module('webfonts')


def static_compile(fam, fmt, profile=False, run=1):
    out = FONT / 'build' / fam
    files = sorted((out / 'instance_ufos').glob('*.ufo'))
    if not files:
        raise RuntimeError('No instance UFOs; run build for this family first')
    filt = 'bwfont.ufo2ft_filters::RobustRemoveOverlapsFilter' + ('(pre=True)' if fmt == 'ttf' else '')
    cmd = [str(PY), '-m', 'cProfile', '-o', str(RESULTS / f'{STAMP}-{fam}-static-@INDEX@.prof'), '-m', 'fontmake'] if profile else [str(FONT / '.venv/bin/fontmake')]
    # Each xargs worker receives a literal path, including whitespace; no shell interpolation.
    if profile:
        # Use indexed inputs so profile output names do not contain source paths.
        worker = 'import subprocess,sys; i,p=sys.argv[1].split("\\t",1); cmd=sys.argv[2:]; cmd[4]=cmd[4].replace("@INDEX@",i); subprocess.run(cmd+["-u",p],check=True)'
        argv = ['xargs','-0','-P',str(ARGS.jobs),'-I{}',str(PY),'-c',worker,'{}',*cmd,'-o',fmt,'--output-dir',str(out/fmt),'--keep-overlaps','--filter',filt]
        payload = '\0'.join(f'{i}\t{p}' for i,p in enumerate(files))+'\0'
    else:
        argv = ['xargs','-0','-P',str(ARGS.jobs),'-I{}',*cmd,'-u','{}','-o',fmt,'--output-dir',str(out/fmt),'--keep-overlaps','--filter',filt]
        payload = '\0'.join(map(str,files))+'\0'
    with (RESULTS / f'{STAMP}-{fam}-{fmt}-{run}.log').open('w') as log:
        subprocess.run(argv, input=payload, text=True, cwd=FONT, env=ENV, stdout=log, stderr=subprocess.STDOUT, check=True)


def build():
    pp, web = modules()
    for run in range(1, ARGS.runs+1):
        for fam in ARGS.families:
            tags = dict(family=fam, run=run)
            ps = pp.PS[fam]
            out = FONT/'build'/fam
            shutil.rmtree(out, ignore_errors=True)
            out.mkdir(parents=True)
            ds = FONT/'sources'/fam/f'{ps}.designspace'
            timed('generate', lambda: command([PY,'tools/generate.py',fam], f'{fam}-generate-{run}'), **tags)
            timed('variable', lambda: command([FONT/'.venv/bin/fontmake','-m',ds,'-o','variable','--output-dir',out/'variable'], f'{fam}-variable-{run}'), **tags)
            timed('make_instances', lambda: command([PY,'tools/make_instances.py',ds,out/'instance_ufos'], f'{fam}-instances-{run}'), **tags)
            for fmt in ('otf','ttf'):
                timed('static_'+fmt, lambda fmt=fmt: static_compile(fam,fmt,run=run), **tags)
            dest = FONT/'fonts'/ps
            shutil.rmtree(dest, ignore_errors=True)
            for sub in ('variable','otf','ttf','woff2','woff'):
                (dest/sub).mkdir(parents=True,exist_ok=True)
            for src in sorted((out/'variable').glob('*.ttf')):
                timed('process_vf',lambda: pp.process_vf((src,dest/'variable'/src.name,dest/'variable'/(src.stem+'.woff2'))),file=src.name,**tags)
            for src in sorted((out/'otf').glob('*.otf')):
                timed('process_otf',lambda: pp.process_otf((src,dest/'otf'/src.name)),file=src.name,**tags)
            # Instrument the actual process_static_ttf implementation, preserving its behavior.
            original_hint, original_save = pp.autohint, pp.TTFont.save
            for src in sorted((out/'ttf').glob('*.ttf')):
                def hint(*a, **kw):
                    hinted=timed('ttfautohint',lambda: original_hint(*a,**kw),file=src.name,**tags)
                    DATA['measurements'][-1]['hinted']=bool(hinted)
                    return hinted
                def save(font, *a, **kw):
                    name = {'woff2':'woff2_encode','woff':'woff_encode'}.get(font.flavor,'ttf_fix_save')
                    return timed(name,lambda: original_save(font,*a,**kw),file=src.name,**tags)
                pp.autohint, pp.TTFont.save = hint, save
                try:
                    timed('process_static_ttf',lambda: pp.process_static_ttf((src,dest/'ttf'/src.name,dest/'woff2'/(src.stem+'.woff2'),dest/'woff'/(src.stem+'.woff'))),file=src.name,**tags)
                finally:
                    pp.autohint, pp.TTFont.save = original_hint, original_save
            timed('package',pp.package,**tags)
            timed('webfonts.write_css',web.write_css,**tags)
            timed('site_data',lambda: command([PY,'tools/site_data.py'],f'{fam}-site-data-{run}'),**tags)
    if ARGS.e2e:
        timed('e2e',lambda: command(['bash','tools/build_all.sh','sans'],'e2e-sans'),family='sans',run=1)


def docs():
    for run in range(1,ARGS.runs+1):
        shutil.rmtree(REPO/'apps/docs/.next',ignore_errors=True)
        for kind in ('cold','warm'):
            timed('docs_'+kind,lambda: command(['bun','run','build'],f'docs-{kind}-{run}',REPO/'apps/docs'),run=run)
        timed('npm_build',lambda: command(['node','scripts/build.mjs'],f'npm-build-{run}',REPO/'packages/npm'),run=run)
        timed('npm_pack',lambda: command(['npm','pack','--dry-run','--json'],f'npm-pack-{run}',REPO/'packages/npm'),run=run)
    DATA['docs_weight'] = page_weight()


class References(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.urls=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='script' and a.get('src'): self.urls.append(a['src'])
        if tag=='link' and a.get('href') and (set(a.get('rel','').split()) & {'stylesheet','preload','modulepreload','prefetch'}): self.urls.append(a['href'])


def page_weight():
    out=REPO/'apps/docs/out'
    if not out.exists(): return {'available':False,'reason':'apps/docs/out absent; run docs first (next.config.ts output=export)'}
    result={'available':True,'export_dir':str(out),'total_bytes':sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}
    index=out/'index.html'
    if not index.exists(): return dict(result,index_missing=True)
    parser=References(); parser.feed(index.read_text())
    files={}; missing=[]
    for url in parser.urls:
        u=urlsplit(url)
        if u.scheme or u.netloc: continue
        path=unquote(u.path)
        if path.startswith('/font/'): path=path[5:]
        p=out/path.lstrip('/')
        if p.is_file(): files[str(p.relative_to(out))]=p.stat().st_size
        else: missing.append(url)
    result.update(html_bytes=index.stat().st_size, referenced_files=files,missing_references=missing,index_referenced_total_bytes=index.stat().st_size+sum(files.values()), scope='Direct HTML script, stylesheet and preload references; excludes lazy chunks and CSS-selected fonts not preloaded.')
    return result


def assets():
    pack=json.loads(capture(['npm','pack','--dry-run','--json','--ignore-scripts'],REPO/'packages/npm'))[0]
    DATA['npm']={k:pack.get(k) for k in ('unpackedSize','entryCount','size','files')}
    for key, value in [('npm_unpacked_bytes',pack['unpackedSize']),('npm_file_count',pack['entryCount'])]:
        DATA['metrics'].append(dict(stage=key,value=value,unit='bytes' if key.endswith('bytes') else 'files'))
    DATA['npm_native']={}
    for package_json in sorted((REPO/'packages/native').glob('*/package.json')):
        package=json.loads(package_json.read_text())
        native_pack=json.loads(capture(['npm','pack','--dry-run','--json','--ignore-scripts'],package_json.parent))[0]
        DATA['npm_native'][package['name']]={k:native_pack.get(k) for k in ('unpackedSize','entryCount','size','files')}
        for key,value,unit in [('unpacked_bytes',native_pack['unpackedSize'],'bytes'),('file_count',native_pack['entryCount'],'files')]:
            DATA['metrics'].append(dict(stage=f"npm_native/{package['name']}/{key}",value=value,unit=unit))
    DATA['font_assets']={}
    for root in (FONT/'fonts',REPO/'apps/docs/public/fonts'):
        formats={}; faces=[]
        for p in sorted(root.rglob('*')):
            if not p.is_file() or p.suffix not in ('.ttf','.otf','.woff','.woff2'): continue
            family=p.relative_to(root).parts[0]; key=f'{family}/{p.suffix[1:]}'
            formats[key]=formats.get(key,0)+p.stat().st_size
            if p.suffix=='.woff2': faces.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,kind='variable' if 'variable' in p.parts else 'static'))
        DATA['font_assets'][str(root)]={'bytes_by_family_format':formats,'woff2_faces':faces,'available':root.exists()}
    css=set((REPO/'packages/npm').glob('*.css')) | set((REPO/'packages/npm/css').glob('*.css')) | {REPO/'apps/docs/public/bloxwap-font.css'}
    DATA['css']=[dict(path=str(p.relative_to(REPO)),bytes=p.stat().st_size,gzip_bytes=len(gzip.compress(p.read_bytes(),mtime=0)),font_faces=len(re.findall(r'@font-face\s*\{',p.read_text()))) for p in sorted(css) if p.exists()]
    public=REPO/'apps/docs/public/fonts/BloxwapSans/variable'
    if not public.exists(): public=FONT/'fonts/BloxwapSans/variable'
    upright=next(iter(sorted(public.glob('BloxwapSans[[]*.woff2'))),None)
    italic=next(iter(sorted(public.glob('BloxwapSans-Italic[[]*.woff2'))),None)
    catalog=REPO/'apps/docs/public/bloxwap-font.css'
    catalog_css=catalog.read_text() if catalog.exists() else ''
    def latin_source(source):
        if source is None: return None
        candidate=source.parent/'subsets'/f'{source.stem}.latin.woff2'
        return candidate if candidate.exists() and f'subsets/{quote(candidate.name)}' in catalog_css else source
    latin_upright,latin_italic=map(latin_source,(upright,italic))
    DATA['latin_page']={'normal_bytes':latin_upright.stat().st_size if latin_upright else None,'normal_italic_bytes':latin_upright.stat().st_size+latin_italic.stat().st_size if latin_upright and latin_italic else None,'files':[str(p) for p in (latin_upright,latin_italic) if p], 'assumption':'Latin text selects CSS-linked core Sans Latin subsets when available, otherwise full variable files; no companion fonts or HTTP overhead.'}
    if upright:
        from fontTools.ttLib import TTFont
        from fontTools import subset
        with TTFont(upright) as f:
            raw=io.BytesIO(); f.flavor=None; f.save(raw); raw.seek(0)
            with TTFont(raw, lazy=True) as sfnt:
                table_sizes={tag:entry.length for tag,entry in sfnt.reader.tables.items()}
            DATA['sans_variable']={'path':str(upright),'glyph_count':len(f.getGlyphOrder()),'cmap_entries':len(f.getBestCmap() or {}),'table_sizes_uncompressed_sfnt_bytes':table_sizes}
            options=subset.Options(); options.layout_features=['*']; options.hinting=True
            sub=subset.Subsetter(options=options); sub.populate(unicodes=subset.parse_unicodes(LATIN)); sub.subset(f)
            target=RESULTS/f'{STAMP}-sans-latin.woff2'; f.flavor='woff2'; f.save(target)
            DATA['sans_variable']['latin_subset']={'path':str(target),'bytes':target.stat().st_size,'unicode_range':LATIN,'layout_features':'*','hinting':True,'variations_preserved':'fvar' in f,'glyph_count':len(f.getGlyphOrder())}
    DATA['docs_weight']=page_weight()
    def metric(name, value, unit='bytes'):
        if value is not None:
            DATA['metrics'].append(dict(stage=name,value=value,unit=unit))
    for root, details in DATA['font_assets'].items():
        label='dist' if root==str(FONT/'fonts') else 'docs'
        for key,value in details['bytes_by_family_format'].items(): metric(label+'/'+key,value)
        for face in details['woff2_faces']: metric(label+'/'+face['path'],face['bytes'])
    for css in DATA['css']:
        metric(css['path'],css['bytes']); metric(css['path']+'/gzip',css['gzip_bytes']); metric(css['path']+'/faces',css['font_faces'],'faces')
    for key in ('normal_bytes','normal_italic_bytes'): metric('latin_page/'+key,DATA['latin_page'][key])
    if 'sans_variable' in DATA:
        font=DATA['sans_variable']
        metric('sans/glyphs',font['glyph_count'],'glyphs'); metric('sans/cmap',font['cmap_entries'],'codepoints')
        for tag,value in font['table_sizes_uncompressed_sfnt_bytes'].items(): metric('sans/table/'+tag,value)
        metric('sans/latin_subset',font['latin_subset']['bytes'])
    for key in ('total_bytes','html_bytes','index_referenced_total_bytes'):
        metric('docs/'+key,DATA['docs_weight'].get(key))


def profile():
    pp,_=modules(); fam=ARGS.family; ps=pp.PS[fam]; out=FONT/'build'/fam
    ds=FONT/'sources'/fam/f'{ps}.designspace'
    if ARGS.stage=='static_ttf':
        timed('profile_static_ttf',lambda:static_compile(fam,'ttf',True),family=fam)
        paths=list(RESULTS.glob(f'{STAMP}-{fam}-static-*.prof'))
    else:
        path=RESULTS/f'{STAMP}-{fam}-{ARGS.stage}.prof'
        target=['tools/generate.py',fam] if ARGS.stage=='generate' else ['-m','fontmake','-m',str(ds),'-o','variable','--output-dir',str(out/'variable')]
        timed('profile_'+ARGS.stage,lambda:command([PY,'-m','cProfile','-o',path,*target],f'profile-{fam}-{ARGS.stage}'),family=fam)
        paths=[path]
    stats=pstats.Stats(*map(str,paths)); stream=io.StringIO(); stats.stream=stream
    for key in ('cumulative','tottime'): stats.sort_stats(key).print_stats(40)
    target=RESULTS/f'{STAMP}-{fam}-{ARGS.stage}.txt'; target.write_text(stream.getvalue()); DATA['profile']={'raw':list(map(str,paths)),'text':str(target)}


def summarize(rows):
    groups={}
    # Sum per-file measurements within each run before computing run medians.
    for row in rows:
        for key,unit in [('wall_seconds','seconds'),('cpu_seconds','CPU seconds'),('children_cpu_seconds','child CPU seconds'),('children_peak_rss_kib','KiB'),('self_peak_rss_kib','KiB')]:
            if key not in row or row.get('status')!='ok': continue
            group=(row.get('family','all'),row['stage'],key,unit)
            run=row.get('run',1); values=groups.setdefault(group,{})
            if 'rss' in key: values[run]=max(values.get(run,0),row[key])
            else: values[run]=values.get(run,0)+row[key]
    return [dict(family=f,stage=s,metric=k,unit=u,median=statistics.median(v.values()),min=min(v.values()),max=max(v.values()),runs=len(v)) for (f,s,k,u),v in groups.items()]


def report():
    rows=[]
    for path in sorted(RESULTS.glob('*.json')):
        obj=json.loads(path.read_text())
        if not isinstance(obj,dict) or obj.get('command')=='report':continue
        # Preserve file/run identity when merging separate executions.
        for row in obj.get('measurements',[]): rows.append(dict(row,run=f'{path.name}:{row.get("run",1)}'))
    DATA['summary']=summarize(rows)
    metric_groups={}
    for path in sorted(RESULTS.glob('*.json')):
        obj=json.loads(path.read_text())
        if not isinstance(obj,dict) or obj.get('command')=='report': continue
        for r in obj.get('metrics',[]):
            metric_groups.setdefault((r['stage'],r['unit']),[]).append(r['value'])
    for (stage,unit),values in metric_groups.items():
        DATA['summary'].append(dict(family='assets',stage=stage,metric='value',unit=unit,median=statistics.median(values),min=min(values),max=max(values),runs=len(values)))
    lines=['# Baseline','', '| Stage | Median | Min | Max | Runs | Unit |','|---|---:|---:|---:|---:|---|']
    for r in DATA['summary']:
        lines.append(f"| {r['family']}/{r['stage']}/{r['metric']} | {r['median']:.4f} | {r['min']:.4f} | {r['max']:.4f} | {r['runs']} | {r['unit']} |")
    (RESULTS/'baseline.md').write_text('\n'.join(lines)+'\n')


def machine():
    def optional(cmd):
        try:return capture(cmd)
        except Exception as e:return str(e)
    cpu=Path('/proc/cpuinfo').read_text() if Path('/proc/cpuinfo').exists() else ''
    mem=Path('/proc/meminfo').read_text() if Path('/proc/meminfo').exists() else ''
    return dict(nproc=os.cpu_count(),available_cpus=len(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,ram=mem.splitlines()[0] if mem else None,cpu_model=next((x.split(':',1)[1].strip() for x in cpu.splitlines() if x.startswith('model name')),platform.processor()),platform=platform.platform(),load_average=os.getloadavg(),python=sys.version,bun=optional(['bun','--version']),node=optional(['node','--version']),fontmake=optional([FONT/'.venv/bin/fontmake','--version']),git_sha=optional(['git','-C',REPO,'rev-parse','HEAD']),jobs=ARGS.jobs,rss_note='Linux ru_maxrss in KiB, lifetime high-water marks, not additive or per-stage deltas. Child CPU is delta RUSAGE_CHILDREN; CPU includes self plus reaped descendants. Nested substage timings overlap parent timings.')


def main():
    global ARGS, REPO, FONT, PY, ENV, STAMP, DATA, RESULTS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=BASE)
    parser.add_argument('--results',type=Path,default=RESULTS,help='Measurement directory (default: bench/results)')
    parser.add_argument('--restore',action='store_true',help='Destructively discard tracked changes under apps/docs/public apps/docs/lib packages; clean only packages/font/build')
    parser.add_argument('--jobs',type=int,default=int(os.environ.get('JOBS','6')))
    subs=parser.add_subparsers(dest='command',required=True)
    b=subs.add_parser('build'); b.add_argument('--families',nargs='+',default=['sans','mono','pixel']); b.add_argument('--runs',type=int,default=1); b.add_argument('--e2e',action='store_true')
    d=subs.add_parser('docs'); d.add_argument('--runs',type=int,default=1)
    subs.add_parser('assets'); p=subs.add_parser('profile'); p.add_argument('--family',default='sans'); p.add_argument('--stage',choices=['generate','variable','static_ttf'],required=True)
    subs.add_parser('report'); ARGS=parser.parse_args()
    if ARGS.jobs<1 or getattr(ARGS,'runs',1)<1:parser.error('jobs and runs must be positive')
    REPO=ARGS.repo.resolve(); RESULTS=ARGS.results.resolve(); FONT=REPO/'packages/font'; PY=FONT/'.venv/bin/python'
    ENV=os.environ.copy(); ENV['PYTHONPATH']=str(FONT/'tools')+os.pathsep+ENV.get('PYTHONPATH',''); ENV['FONT_PYTHON']=str(PY); ENV['JOBS']=str(ARGS.jobs)
    STAMP=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'); RESULTS.mkdir(parents=True,exist_ok=True)
    DATA=dict(license='OFL-1.1',command=ARGS.command,timestamp=STAMP,repo=str(REPO),environment={k:ENV.get(k) for k in ('JOBS','FONT_PYTHON','PYTHONPATH','NEXT_PUBLIC_BASE_PATH','NODE_ENV')},arguments={k:str(v) if isinstance(v,Path) else v for k,v in vars(ARGS).items()},machine=machine(),measurements=[],metrics=[])
    try:
        globals()[ARGS.command]()
    except Exception as e:
        DATA['error']=repr(e); raise
    finally:
        if ARGS.restore:
            try:
                capture(['git','-C',REPO,'checkout','--','apps/docs/public','apps/docs/lib','packages'])
                DATA['restore_clean']=capture(['git','-C',REPO,'clean','-fdx','--','packages/font/build/'])
            except Exception as e: DATA['restore_error']=repr(e)
        if ARGS.command!='report': DATA['summary']=summarize(DATA['measurements'])
        path=RESULTS/f'{ARGS.command}-{STAMP}.json'; path.write_text(json.dumps(DATA,indent=2)+'\n'); print(path)


if __name__=='__main__':main()
