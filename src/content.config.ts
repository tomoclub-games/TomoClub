import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const articles = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    category: z.string(),
    cover: z.string(),
    alt: z.string().optional(),
    gradient: z.enum(['teal', 'gold', 'crimson', 'slate']).optional(),
    description: z.string(),
  }),
});

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    slug: z.string().optional(),
    category: z.string(),
    description: z.string(),
    cover: z.string(),
  }),
});

const podcasts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/podcasts' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    speaker: z.string(),
    date: z.string(),
    duration: z.string(),
    thumbnail: z.string().optional(),
    description: z.string(),
  }),
});

export const collections = { articles, blog, podcasts };
