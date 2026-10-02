// Compact concept index for client-side pickers (the suggest-an-edit form).
import type { APIRoute } from 'astro';
import { vocab } from '../lib/vocab';

export const GET: APIRoute = () =>
  new Response(JSON.stringify(Object.values(vocab.concepts).map((c) => [c.curie, c.label])), {
    headers: { 'Content-Type': 'application/json' },
  });
