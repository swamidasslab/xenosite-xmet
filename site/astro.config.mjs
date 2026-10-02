// Generic vocabulary site. All project specifics come from the generated data
// contract (src/generated/vocab.json, written by tools/sitegen from the site config).
import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { unified } from '@astrojs/markdown-remark';
import remarkVocab from './src/lib/remark-vocab.mjs';

const contract = JSON.parse(readFileSync(new URL('./src/generated/vocab.json', import.meta.url), 'utf8'));
const { url, base } = contract.site;

export default defineConfig({
  site: new URL(url).origin,
  base: base || '/',
  trailingSlash: 'always',
  integrations: [sitemap({ filter: (page) => !page.includes('/404') })],
  markdown: { processor: unified({ remarkPlugins: [remarkVocab] }) },
  vite: { plugins: [tailwindcss()] },
});
