'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { getAllCollections } from '@/lib/collections';
import CollectionTabBar from '@/components/collections/CollectionTabBar';

export default function CollectionsLanding() {
  const collections = getAllCollections();

  return (
    <>
      {/* Header */}
      <header className="relative py-24 px-4 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <p className="text-[#B76E79] text-xs tracking-[0.3em] uppercase mb-4">
            SkyyRose
          </p>
          <h1 className="text-5xl md:text-7xl font-display text-white mb-6">
            Collections
          </h1>
          <p className="text-white/40 max-w-md mx-auto text-sm leading-relaxed">
            Three worlds, three stories. Each collection is an immersive
            journey into luxury fashion.
          </p>
        </motion.div>

        {/* Decorative line */}
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="w-16 h-px bg-[#B76E79] mx-auto mt-8"
        />
      </header>

      {/* Collection Cards */}
      <section className="px-4 md:px-8 pb-28 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {collections.map((collection, index) => (
            <CollectionPreviewCard
              key={collection.slug}
              name={collection.name}
              tagline={collection.tagline}
              description={collection.description}
              heroImage={collection.heroImage}
              accentColor={collection.accentColor}
              slug={collection.slug}
              productCount={collection.scenes.reduce(
                (sum, s) => sum + s.products.length,
                0
              )}
              sceneCount={collection.scenes.length}
              index={index}
            />
          ))}
        </div>
      </section>

      {/* Brand Footer */}
      <footer className="border-t border-white/5 py-12 px-4 text-center pb-24">
        <p className="text-white/20 text-xs tracking-[0.2em] uppercase">
          Where Love Meets Luxury
        </p>
        <p className="text-white/10 text-xs mt-2 tracking-wider">
          SkyyRose LLC
        </p>
      </footer>

      <CollectionTabBar />
    </>
  );
}

function CollectionPreviewCard({
  name,
  tagline,
  description,
  heroImage,
  accentColor,
  slug,
  productCount,
  sceneCount,
  index,
}: {
  name: string;
  tagline: string;
  description: string;
  heroImage: string;
  accentColor: string;
  slug: string;
  productCount: number;
  sceneCount: number;
  index: number;
}) {
  const [imageError, setImageError] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay: index * 0.15 }}
    >
      <Link
        href={`/collections/${slug}`}
        className="group block relative overflow-hidden rounded-xl border border-white/5 hover:border-white/10 transition-all duration-500"
      >
        {/* Image */}
        <div className="relative aspect-[3/4] overflow-hidden bg-gradient-to-b from-white/[0.03] to-transparent">
          {!imageError ? (
            <Image
              src={heroImage}
              alt={`${name} collection`}
              fill
              sizes="(max-width: 768px) 100vw, 33vw"
              className="object-cover transition-transform duration-700 group-hover:scale-105"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div
                className="w-24 h-24 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${accentColor}10` }}
              >
                <span
                  className="text-4xl font-display"
                  style={{ color: accentColor }}
                >
                  {name.charAt(0)}
                </span>
              </div>
            </div>
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

          {/* Hover accent line */}
          <motion.div
            className="absolute top-0 left-0 right-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
            style={{ backgroundColor: accentColor }}
          />
        </div>

        {/* Content */}
        <div className="absolute bottom-0 left-0 right-0 p-6">
          <p
            className="text-xs tracking-[0.2em] uppercase mb-2"
            style={{ color: accentColor }}
          >
            {tagline}
          </p>
          <h2 className="text-2xl font-display text-white mb-2">{name}</h2>
          <p className="text-white/40 text-sm leading-relaxed line-clamp-2 mb-4">
            {description}
          </p>

          {/* Stats */}
          <div className="flex gap-4 text-white/25 text-xs tracking-wider">
            <span>{productCount} pieces</span>
            <span>&middot;</span>
            <span>
              {sceneCount} {sceneCount === 1 ? 'scene' : 'scenes'}
            </span>
          </div>

          {/* Enter CTA */}
          <div
            className="mt-4 flex items-center gap-2 text-sm tracking-[0.1em] opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style={{ color: accentColor }}
          >
            <span>Enter Experience</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
