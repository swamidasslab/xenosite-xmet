// Remark plugin for content Markdown:
//   [[slug]]          → link to that concept, labelled with its current preferred label
//   {{stats.name}}    → a live value from the data contract (any dotted path)
//   relative links    → resolved against the site base (write `browse/`, not `/browse/`)
import { readFileSync } from 'node:fs';

const contract = JSON.parse(readFileSync(new URL('../generated/vocab.json', import.meta.url), 'utf8'));
const base = (contract.site.base || '').replace(/\/$/, '');
const TOKEN = /\[\[([^\]\s]+)\]\]|\{\{\s*([\w.]+)\s*\}\}/g;

function lookup(path) {
  const v = path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), contract);
  return typeof v === 'number' ? v.toLocaleString('en-US') : v == null ? `{{${path}}}` : String(v);
}

function expand(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(TOKEN)) {
    if (m.index > last) out.push({ type: 'text', value: text.slice(last, m.index) });
    if (m[1]) {
      const c = contract.concepts[m[1]];
      out.push(
        c
          ? { type: 'link', url: `${base}/term/${c.slug}/`, title: c.curie, data: { hProperties: { className: ['term-link'] } }, children: [{ type: 'text', value: c.label }] }
          : { type: 'text', value: m[0] },
      );
    } else {
      out.push({ type: 'text', value: lookup(m[2]) });
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push({ type: 'text', value: text.slice(last) });
  return out;
}

function walk(node) {
  if (node.type === 'link' && node.url && !/^([a-z][a-z0-9+.-]*:|\/|#|\?)/i.test(node.url)) {
    node.url = `${base}/${node.url}`;
  }
  if (!node.children) return;
  const next = [];
  for (const child of node.children) {
    if (child.type === 'text' && TOKEN.test(child.value)) {
      TOKEN.lastIndex = 0;
      next.push(...expand(child.value));
    } else {
      walk(child);
      next.push(child);
    }
  }
  node.children = next;
}

export default function remarkVocab() {
  return (tree) => walk(tree);
}
