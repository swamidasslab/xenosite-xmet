// Typed access to the data contract written by tools/sitegen.
import data from '../generated/vocab.json';
import { uiStrings } from './ui';

export interface Relation {
  key: string;
  direction: 'out' | 'in';
  target?: string;
  implied?: boolean;
  external?: boolean;
  curie?: string;
  iri?: string;
}
export interface Flag { check: string; severity: 'error' | 'warn' | 'info' | string; detail: string; refs?: string[]; term?: string }
export interface Mapping { source: string; predicate: string; object: string; object_label: string; justification: string }
export interface Concept {
  slug: string; curie: string; iri: string; label: string; definition: string; synonyms: string[];
  parents: string[]; children: string[]; ancestors: string[]; depth: number; descendants: number;
  relations: Relation[]; extras: Record<string, unknown>; has_sidecar: boolean; source_line: number | null;
  flags: Flag[]; mappings: Mapping[];
}
export interface RelationDef {
  key: string; label: string; predicate?: string; inverse_label?: string; inverse?: string;
  symmetric?: boolean; external?: boolean;
}

export const vocab = data as unknown as {
  site: {
    title: string; tagline?: string; description?: string; url: string; base: string; logo?: string;
    repo: { url?: string; branch?: string };
    theme?: { accent?: string; neutral?: string };
    organization?: { name: string; url?: string };
    parent_site?: { name: string; url?: string };
    license?: { name: string; url?: string };
  };
  ui: Record<string, string>;
  paths: Record<string, string>;
  sidecar_template: string;
  edits?: { patches_dir?: string };
  scheme: { iri: string; label: string; definition: string };
  namespace: string; curie_prefix: string; revision: string; generated: string;
  relations: RelationDef[];
  extra_fields: Record<string, { label?: string; display?: string }>;
  checks: { check: string; severity: string; count: number }[];
  mappings: { show: boolean; sources: { label: string; path: string; count: number }[] };
  downloads: { label: string; file: string; source: string; bytes: number }[];
  term_rdf: boolean;
  stats: Record<string, any>;
  roots: string[];
  concepts: Record<string, Concept>;
};

export const ui = uiStrings(vocab.ui);
export const concepts = vocab.concepts;
export const relationDefs = Object.fromEntries(vocab.relations.map((r) => [r.key, r]));
export const SEVERITIES = ['error', 'warn', 'info'] as const;

const base = (vocab.site.base || '').replace(/\/$/, '');
/** Site-internal URL for a path like 'browse/' or 'term/123/'. */
export const href = (path = '') => `${base}/${path.replace(/^\//, '')}`;
export const termHref = (slug: string) => href(`term/${slug}/`);
export const absolute = (path = '') => `${vocab.site.url}/${path.replace(/^\//, '')}`;
export const concept = (slug: string) => concepts[slug];

export function relationLabel(key: string, direction: 'out' | 'in'): string {
  const d = relationDefs[key];
  if (!d) return key;
  return direction === 'in' ? d.inverse_label || `${d.label} (inverse)` : d.label;
}

/** Local name of a predicate IRI, used as an anchor on the schema page. */
export const localName = (iri = '') => iri.split(/[#/]/).pop() || iri;

export function repoLinks(c: Concept) {
  const { url, branch = 'main' } = vocab.site.repo;
  if (!url) return {};
  const p = vocab.paths;
  return {
    source: `${url}/blob/${branch}/${p.source}${c.source_line ? `#L${c.source_line}` : ''}`,
    notes: c.has_sidecar
      ? `${url}/edit/${branch}/${p.sidecars_rel}/${c.slug}.md`
      : `${url}/new/${branch}/${p.sidecars_rel}?filename=${encodeURIComponent(c.slug + '.md')}&value=${encodeURIComponent(vocab.sidecar_template)}`,
    issue: `${url}/issues/new?title=${encodeURIComponent(`[${c.curie}] ${c.label}`)}&body=${encodeURIComponent(`Concept: ${c.iri}\n\n`)}`,
  };
}

/** Top-level branch (a child of a root) that a concept sits under; roots and branches map to themselves. */
export const branchOf = (c: Concept): string => (c.ancestors.length >= 2 ? c.ancestors[1] : c.slug);

/** Page explaining one quality check on one concept. */
export const issueHref = (slug: string, check: string) => href(`term/${slug}/issue/${check}/`);
