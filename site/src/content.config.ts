// Content collections. Directories come from the site config via the data contract,
// so all prose stays outside the site code.
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import data from './generated/vocab.json';

const paths = (data as any).paths as Record<string, string>;
// A missing directory (e.g. no per-concept notes yet) just yields an empty collection.
const dir = (p: string) => new URL(`file://${p}/`);

const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: dir(paths.pages) }),
  schema: z.object({
    title: z.string(),
    headline: z.string().optional(),
    summary: z.string().optional(),
    nav_order: z.number().optional(),
    footer: z.boolean().optional(),
  }),
});

const checks = defineCollection({
  loader: glob({ pattern: '*.md', base: dir(paths.checks) }),
  schema: z.object({ title: z.string() }),
});

// Optional per-concept notes; frontmatter fields are already merged into the contract.
const notes = defineCollection({
  loader: glob({ pattern: ['*.md', '!README.md'], base: dir(paths.sidecars) }),
  schema: z.looseObject({}),
});

export const collections = { pages, checks, notes };
