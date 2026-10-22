#!/usr/bin/env python3
"""
potatolib.py - KiCad symbol library tooling.

    updt_symbols     rebuild every library that has a CSV in gen/
    updt_positions   normalize field layout in every hand-made library
    updt_tables      write sym-lib-table / fp-lib-table for a project
    all              updt_symbols + updt_positions

A library is GENERATED when gen/<name>.csv exists, HAND-MADE otherwise.
updt_positions never touches a generated library.

Field layout (positions, fonts, order) comes from config.json for both
commands, so generated and hand-made symbols always look the same.

updt_tables takes a project directory and writes its KiCad library tables
from whatever is on disk here. Entries that do not point into this library
are preserved, so official/global libraries are never touched.
"""

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


# S-expressions
SINGLE_LINE = {
    'pts', 'xy', 'at', 'start', 'end', 'mid', 'stroke', 'fill', 'effects',
    'font', 'justify', 'offset', 'size', 'hide', 'do_not_autoplace', 'extends',
}


def tokenize(text):
    tokens, i = [], 0
    while i < len(text):
        c = text[i]
        if c in ' \t\n\r':
            i += 1
        elif c in '()':
            tokens.append(c)
            i += 1
        elif c == '"':
            j, out = i + 1, []
            while j < len(text):
                if text[j] == '\\' and j + 1 < len(text):
                    out.append(text[j + 1])
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    out.append(text[j])
                    j += 1
            tokens.append('"' + ''.join(out) + '"')
            i = j + 1
        else:
            j = i
            while j < len(text) and text[j] not in ' \t\n\r()"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse_sexpr(tokens, pos=0):
    if tokens[pos] == '(':
        pos += 1
        node = []
        while tokens[pos] != ')':
            child, pos = parse_sexpr(tokens, pos)
            node.append(child)
        return node, pos + 1
    return tokens[pos], pos + 1


def load_sym(path):
    tree, _ = parse_sexpr(tokenize(Path(path).read_text(encoding='utf-8')), 0)
    return tree


def serialize(node, indent=0):
    if isinstance(node, str):
        return node
    if not node:
        return '()'
    if isinstance(node[0], str) and node[0] in SINGLE_LINE:
        return '(' + ' '.join(serialize(c, 0) for c in node) + ')'
    parts = [serialize(c, indent + 1) for c in node]
    single = '(' + ' '.join(parts) + ')'
    if len(single) <= 100 and '\n' not in single:
        return single
    pad = '\t' * (indent + 1)
    lines = ['(' + parts[0]] + [pad + p for p in parts[1:]]
    lines[-1] += ')'
    return '\n'.join(lines)


def dump_lib(symbols):
    tree = ['kicad_symbol_lib', ['version', '20241209'],
            ['generator', '"potatolib.py"'], ['generator_version', '"1.0"']]
    return serialize(tree + symbols, 0) + '\n'


# Symbol structure
HEADER_NODES = ('pin_numbers', 'pin_names', 'exclude_from_sim',
                'in_bom', 'on_board')
GRAPHIC_NODES = ('polyline', 'arc', 'circle', 'rectangle', 'bezier')


def top_symbols(tree):
    return [n for n in tree if isinstance(n, list) and n and n[0] == 'symbol']


def name_of(sym):
    return sym[1].strip('"')


def find_symbol(tree, name):
    for s in top_symbols(tree):
        if name_of(s) == name:
            return s
    return None


def is_derived(sym):
    return any(isinstance(n, list) and n and n[0] == 'extends' for n in sym)


def property_values(sym):
    """Existing field values, in the order they appear."""
    return {n[1].strip('"'): n[2].strip('"')
            for n in sym if isinstance(n, list) and n and n[0] == 'property'}


def without_properties(sym):
    return [n for n in sym if not (isinstance(n, list) and n and n[0] == 'property')]


def rename_subsymbols(sym, old, new):
    for n in sym:
        if isinstance(n, list) and n and n[0] == 'symbol':
            sub = n[1].strip('"')
            if sub.startswith(old + '_'):
                n[1] = f'"{new}{sub[len(old):]}"'


def compute_y_max(sym):
    """Top of the drawn body, ignoring private helper graphics."""
    ys = []
    for n in sym:
        if isinstance(n, list) and n and n[0] == 'symbol':
            for child in n[1:]:
                if (isinstance(child, list) and child
                        and child[0] in GRAPHIC_NODES and 'private' not in child):
                    ys.extend(_collect_y(child))
    return max(ys) if ys else 1.016


def _collect_y(node):
    ys = []
    if isinstance(node, list):
        if node and node[0] in ('xy', 'start', 'end', 'mid', 'center') and len(node) >= 3:
            try:
                ys.append(float(node[2]))
            except ValueError:
                pass
        for child in node:
            ys.extend(_collect_y(child))
    return ys


def apply_pin_style(sym, cfg):
    pn = 'yes' if cfg['pin_numbers'].get('hide', True) else 'no'
    pm = 'yes' if cfg['pin_names'].get('hide', True) else 'no'
    for n in sym:
        if isinstance(n, list) and n:
            if n[0] == 'pin_numbers':
                n.clear()
                n += ['pin_numbers', ['hide', pn]]
            elif n[0] == 'pin_names':
                n.clear()
                n += ['pin_names', ['hide', pm]]

    pc = cfg.get('pin_text') or {}
    sizes = {}
    if 'name_font_size' in pc:
        sizes['name'] = str(pc['name_font_size'])
    if 'number_font_size' in pc:
        sizes['number'] = str(pc['number_font_size'])
    if sizes:
        _set_pin_fonts(sym, sizes)


def _set_pin_fonts(node, sizes):
    if not isinstance(node, list):
        return
    if node and node[0] == 'pin':
        for child in node:
            if isinstance(child, list) and child and child[0] in sizes:
                s = sizes[child[0]]
                for eff in child:
                    if isinstance(eff, list) and eff and eff[0] == 'effects':
                        for fnt in eff:
                            if isinstance(fnt, list) and fnt and fnt[0] == 'font':
                                for sz in fnt:
                                    if isinstance(sz, list) and sz and sz[0] == 'size':
                                        sz[1] = sz[2] = s
    for child in node:
        _set_pin_fonts(child, sizes)


def assemble(sym, properties):
    """symbol name + header flags + properties + everything else."""
    head, rest = [sym[0], sym[1]], []
    for n in sym[2:]:
        target = head if isinstance(n, list) and n and n[0] in HEADER_NODES else rest
        target.append(n)
    return head + properties + rest


# Field layout  (the one rule both commands obey)
def build_property(name, value, x, y, size, visible, justify=None, pin=False):
    s = str(size)
    effects = ['effects', ['font', ['size', s, s]]]
    if justify:
        effects.append(['justify', justify])
    if not visible:
        effects.append(['hide', 'yes'])
    node = ['property', f'"{name}"', f'"{value}"', ['at', str(x), str(y), '0'], effects]
    if pin:
        node.append(['do_not_autoplace'])
    return node


def field_nodes(values, cfg, y_max, with_reference=True, ref_default='U?'):
    """
    Reference and Value sit above the body; every other field goes into the
    fixed column to the right, one row per field, in config order, then any
    extra fields in the order they were given. Missing values become "".
    """
    rc, vc, hc = cfg['reference'], cfg['value'], cfg['hidden_fields']
    autoplace = cfg.get('allow_kicad_autoplace', False)
    out = []

    if with_reference:
        out.append(build_property(
            'Reference', values.get('Reference', ref_default),
            rc['x'], round(y_max + rc['offset_y_above_graphic'], 6),
            rc['font_size'], rc.get('visible', True),
            pin=rc.get('do_not_autoplace', True) and not autoplace))

    out.append(build_property(
        'Value', values.get('Value', ''),
        vc['x'], round(y_max + vc['offset_y_above_graphic'], 6),
        vc['font_size'], vc.get('visible', True),
        pin=vc.get('do_not_autoplace', True) and not autoplace))

    ordered = list(cfg.get('fields_order', []))
    extras = [k for k in values
              if k not in ordered and k not in ('Reference', 'Value') and values[k]]

    for i, fname in enumerate(ordered + extras):
        out.append(build_property(
            fname, values.get(fname, ''),
            hc['start_x'], round(hc['start_y'] + hc['step_y'] * i, 6),
            hc['font_size'], False, justify=hc.get('justify', 'left')))
    return out


# Sources
def discover(gen_dir, sym_dir):
    """(generated, handmade) - a library is generated iff its CSV exists."""
    csvs = sorted(p for p in gen_dir.glob('*.csv'))
    generated = [(c, sym_dir / f'{c.stem}.kicad_sym') for c in csvs]
    owned = {c.stem for c in csvs}
    handmade = [p for p in sorted(sym_dir.glob('*.kicad_sym')) if p.stem not in owned]
    return generated, handmade


def read_rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        rows = [{k.strip(): (v or '').strip() for k, v in r.items() if k}
                for r in csv.DictReader(f)]
    rows = [r for r in rows if r.get('MPN')]
    rows.sort(key=lambda r: r['MPN'])
    return rows


def kb(n):
    return f'{n / 1024:.1f} KB'


def plural(n, one, many):
    return f'{n} {one if n == 1 else many}'


# Library tables
TABLE_SPECS = {
    'sym': ('sym_lib_table', 'sym-lib-table'),
    'fp': ('fp_lib_table', 'fp-lib-table'),
}


def parse_table(path):
    """Existing (nickname, uri) pairs, or [] if the file is absent/unreadable."""
    if not path.exists():
        return []
    try:
        tree, _ = parse_sexpr(tokenize(path.read_text(encoding='utf-8')), 0)
    except Exception:
        return []
    out = []
    for node in tree:
        if isinstance(node, list) and node and node[0] == 'lib':
            fields, flags = {}, []
            for n in node[1:]:
                if isinstance(n, list) and len(n) > 1:
                    fields[n[0]] = n[1].strip('"')
                elif isinstance(n, list) and len(n) == 1:
                    flags.append(n[0])          # (hidden), (disabled), ...
            if 'name' in fields:
                out.append((fields['name'], fields.get('uri', ''), flags))
    return out


def render_table(kind, entries):
    token = TABLE_SPECS[kind][0]
    lines = [f'({token}', '  (version 7)']
    for nick, uri, flags in entries:
        tail = ''.join(f'({f})' for f in flags)
        lines.append(f'  (lib (name "{nick}")(type "KiCad")(uri "{uri}")'
                     f'(options "")(descr ""){tail})')
    return '\n'.join(lines) + '\n)\n'


def wanted_entries(kind, gen_dir, sym_dir, cfg, with_templates):
    prefix = cfg.get('lib_prefix', '')
    base = cfg.get('lib_uri_base', '${KIPRJMOD}/../lib')
    if kind == 'fp':
        return [(f'{prefix}footprints', f'{base}/footprints', [])]
    out = [(prefix + p.stem, f'{base}/symbols/{p.name}', [])
           for p in sorted(sym_dir.glob('*.kicad_sym'))]
    if with_templates:
        # last, and hidden: templates must not be placeable in a schematic
        out.append(('_templates', f'{base}/gen/_templates.kicad_sym', ['hidden']))
    return out


def cmd_updt_tables(cfg, args):
    base = cfg.get('lib_uri_base', '${KIPRJMOD}/../lib')
    marker = base.rstrip('/') + '/'
    project = Path(args.project).resolve()
    target = project / 'sources' if (project / 'sources').is_dir() else project

    if not list(target.glob('*.kicad_pro')):
        print(f'error: no .kicad_pro in {target}', file=sys.stderr)
        print('       is this a KiCad project? use --project to point elsewhere.',
              file=sys.stderr)
        return [f'updt_tables: {target} is not a KiCad project']

    print(f'project     {project}')
    print(f'tables in   {target}\n')

    problems = []
    for kind in ('sym', 'fp'):
        path = target / TABLE_SPECS[kind][1]
        old = parse_table(path)
        foreign = [e for e in old if not e[1].startswith(marker)]
        mine = wanted_entries(kind, args.gen, args.symbols, cfg,
                              args.templates_too)
        text = render_table(kind, foreign + mine)

        if not path.exists():
            state = 'created'
        elif path.read_text(encoding='utf-8') == text:
            state = 'unchanged'
        else:
            state = 'updated'
        if state != 'unchanged' and not args.dry_run:
            path.write_text(text, encoding='utf-8')

        note = f'{len(mine)} own'
        if foreign:
            note += f', {len(foreign)} kept'
        print(f'  {TABLE_SPECS[kind][1]:<16} {note:<20} {state}')
        if args.verbose:
            for nick, _, flags in foreign:
                extra = ' ' + ' '.join(flags) if flags else ''
                print(f'                   = {nick}{extra}  (kept)')
            for nick, _, flags in mine:
                extra = ' ' + ' '.join(flags) if flags else ''
                print(f'                   + {nick}{extra}')

    if args.dry_run:
        print('\n[dry run]')
    return problems


# Commands
def cmd_updt_symbols(cfg, args):
    templates = load_sym(args.templates)
    tnames = {name_of(s) for s in top_symbols(templates)}
    prefix = cfg.get('base_prefix', '_')

    print(f'templates   {len(tnames)} loaded from {Path(args.templates).name}')
    print(f'config      {len(cfg.get("fields_order", []))} fields: '
          f'{", ".join(cfg.get("fields_order", []))}\n')

    generated, _ = discover(args.gen, args.symbols)
    if args.only:
        generated = [g for g in generated if g[0].stem in args.only]

    total, problems = 0, []
    for csv_path, out_path in generated:
        rows = read_rows(csv_path)
        symbols, bases, used = [], [], {}

        seen = set()
        for r in rows:
            if r['MPN'] in seen:
                problems.append(f'{csv_path.name}: duplicate MPN {r["MPN"]!r}')
            seen.add(r['MPN'])

        for tname in sorted({r.get('Symbol', '') for r in rows if r.get('Symbol')}):
            if tname not in tnames:
                problems.append(f'{csv_path.name}: no template {tname!r}')
                continue
            base = make_base(find_symbol(templates, tname), tname, prefix, cfg)
            bases.append(base)
            used[tname] = compute_y_max(base)

        for r in rows:
            tname = r.get('Symbol', '')
            if tname in used:
                symbols.append(make_derived(r, tname, prefix, cfg, used[tname]))
            else:
                symbols.append(make_standalone(r, cfg))

        old = out_path.stat().st_size if out_path.exists() else 0
        text = dump_lib(bases + symbols)
        if not args.dry_run:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding='utf-8')
        total += len(rows)

        blist = ', '.join(name_of(b) for b in bases[:3])
        if len(bases) > 3:
            blist += f', +{len(bases) - 3}'
        size = f'{kb(old)} -> {kb(len(text))}' if old else kb(len(text))
        print(f'  {csv_path.stem:<14} {len(rows):>3} parts  '
              f'{len(bases):>2} base{"s" if len(bases) != 1 else " "} '
              f'({blist})  {size}')

    print(f'\n{total} symbols in {plural(len(generated), "library", "libraries")}'
          + ('   [dry run]' if args.dry_run else ''))
    return problems


def make_base(template, tname, prefix, cfg):
    sym = copy.deepcopy(template)
    base = prefix + tname
    sym[1] = f'"{base}"'
    y_max = compute_y_max(sym)
    ref = property_values(template).get('Reference', 'U?')
    sym = without_properties(sym)
    rename_subsymbols(sym, tname, base)
    apply_pin_style(sym, cfg)
    return assemble(sym, field_nodes({'Reference': ref}, cfg, y_max,
                                     ref_default=ref)[:2])


def make_derived(row, tname, prefix, cfg, y_max):
    sym = ['symbol', f'"{row["MPN"]}"', ['extends', f'"{prefix}{tname}"']]
    values = {k: v for k, v in row.items() if k != 'Symbol'}
    return sym + field_nodes(values, cfg, y_max, with_reference=False)


def make_standalone(row, cfg):
    y_max = cfg['reference']['offset_y_above_graphic']
    sym = ['symbol', f'"{row["MPN"]}"',
           ['pin_numbers', ['hide', 'yes']], ['pin_names', ['hide', 'yes']],
           ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes']]
    values = {k: v for k, v in row.items() if k != 'Symbol'}
    return sym + field_nodes(values, cfg, y_max)


def cmd_updt_positions(cfg, args):
    generated, handmade = discover(args.gen, args.symbols)
    targets = handmade + ([Path(args.templates)] if args.templates_too else [])
    if args.only:
        targets = [p for p in targets if p.stem in args.only]

    print(f'config      {len(cfg.get("fields_order", []))} fields: '
          f'{", ".join(cfg.get("fields_order", []))}\n')

    changed_total = 0
    for path in targets:
        tree = load_sym(path)
        out, changed, derived, names = [], 0, 0, []
        for node in tree:
            if not (isinstance(node, list) and node and node[0] == 'symbol'):
                out.append(node)
                continue
            if is_derived(node):
                out.append(node)
                derived += 1
                continue
            before = serialize(node)
            fixed = reposition(node, cfg)
            if serialize(fixed) != before:
                changed += 1
                names.append(name_of(node))
            out.append(fixed)

        n = sum(1 for x in out if isinstance(x, list) and x and x[0] == 'symbol')
        if changed and not args.dry_run:
            path.write_text(dump_lib([x for x in out if isinstance(x, list)
                                      and x and x[0] == 'symbol']), encoding='utf-8')
        changed_total += changed

        note = f'{changed} changed' if changed else 'unchanged'
        if derived:
            note += f', {derived} derived skipped'
        print(f'  {path.stem:<14} {n:>3} {"symbol " if n == 1 else "symbols"}   {note}')
        if args.verbose and names:
            for nm in names:
                print(f'                   - {nm}')

    skipped = ', '.join(c.stem for c, _ in generated)
    if skipped:
        print(f'\nskipped {plural(len(generated), "generated library", "generated libraries")} '
              f'({skipped})')
    print(f'{changed_total} {"symbol" if changed_total == 1 else "symbols"} changed'
          + ('   [dry run]' if args.dry_run else ''))
    return []


def reposition(sym, cfg):
    sym = copy.deepcopy(sym)
    y_max = compute_y_max(sym)
    values = property_values(sym)
    ref = values.get('Reference', 'U?')
    sym = without_properties(sym)
    apply_pin_style(sym, cfg)
    return assemble(sym, field_nodes(values, cfg, y_max, ref_default=ref))


# Main
def main():
    ap = argparse.ArgumentParser(
        description='KiCad symbol library tooling.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='updt_symbols rebuilds libraries from CSVs; updt_positions\n'
               'normalizes hand-made ones; updt_tables --project <dir> writes\n'
               'that project sym-lib-table and fp-lib-table.')
    ap.add_argument('command',
                    choices=['updt_symbols', 'updt_positions', 'updt_tables', 'all'])
    ap.add_argument('--gen', type=Path, default=HERE)
    ap.add_argument('--symbols', type=Path, default=HERE.parent / 'symbols')
    ap.add_argument('--templates', default=str(HERE / '_templates.kicad_sym'))
    ap.add_argument('--config', default=str(HERE / 'config.json'))
    ap.add_argument('--project', type=Path, default=HERE.parent.parent,
                    help='project directory for updt_tables '
                         '(default: two levels up from this script)')
    ap.add_argument('--only', nargs='+', metavar='NAME',
                    help='restrict to these library names')
    ap.add_argument('--no-templates', dest='templates_too', action='store_false',
                    help='leave _templates.kicad_sym alone in updt_positions')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('-v', '--verbose', action='store_true')
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding='utf-8'))
    problems = []
    if args.command in ('updt_symbols', 'all'):
        problems += cmd_updt_symbols(cfg, args)
    if args.command == 'all':
        print()
    if args.command in ('updt_positions', 'all'):
        problems += cmd_updt_positions(cfg, args)
    if args.command == 'updt_tables':
        problems += cmd_updt_tables(cfg, args)

    if problems:
        print(f'\n{len(problems)} problem(s):')
        for p in problems:
            print(f'  ! {p}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
