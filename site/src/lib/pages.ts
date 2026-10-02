import { getEntry } from 'astro:content';

/** Title + summary of a content page, for <head> metadata of app pages. */
export async function pageMeta(id: string, fallback: string) {
  const e = await getEntry('pages', id);
  return { title: e?.data.title ?? fallback, description: e?.data.summary };
}

/** Content pages rendered by dedicated app routes rather than the generic page route. */
export const APP_PAGES = new Set(['index', 'browse', 'search', 'quality', 'schema', 'downloads']);
