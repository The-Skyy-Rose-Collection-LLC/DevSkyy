(() => {
  'use strict';

  const root = document.documentElement;
  const body = document.body;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const header = document.querySelector('[data-site-header]');
  const menuButton = document.querySelector('[data-sr2-menu]');
  const menu = document.querySelector('[data-sr2-nav]');

  root.classList.add('sr2-motion-ready');

  const saveData = Boolean(navigator.connection?.saveData);
  document.querySelectorAll('[data-brand-spin]').forEach((video) => {
    if (reducedMotion || saveData) {
      video.preload = 'none';
      video.pause();
      return;
    }

    const playback = video.play();
    if (playback) playback.catch(() => {});
  });

  const setMenu = (open) => {
    if (!menuButton || !menu) return;
    menu.classList.toggle('is-open', open);
    menuButton.setAttribute('aria-expanded', String(open));
    body.classList.toggle('sr2-nav-open', open);
  };

  if (menuButton && menu) {
    menuButton.addEventListener('click', () => {
      setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
    });

    menu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => setMenu(false));
    });

    document.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape' || menuButton.getAttribute('aria-expanded') !== 'true') return;
      setMenu(false);
      menuButton.focus();
    });
  }

  if (header) {
    let previousY = window.scrollY;
    let ticking = false;

    const updateHeader = () => {
      const currentY = window.scrollY;
      header.classList.toggle('is-scrolled', currentY > 48);
      header.classList.toggle(
        'is-hidden',
        currentY > previousY && currentY > 500 && !body.classList.contains('sr2-nav-open')
      );
      previousY = currentY;
      ticking = false;
    };

    window.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(updateHeader);
    }, { passive: true });
  }

  const revealTargets = document.querySelectorAll(
    '.sr2-section-head, .sr2-product, .sr2-collection-intro, .sr2-manifesto__scroll > *, .sr2-preorder-steps article, .sr2-contact-grid > *, .sr2-service-links a, .sr2-image-reveal'
  );

  if ('IntersectionObserver' in window && !reducedMotion) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-seen');
        observer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    revealTargets.forEach((target) => {
      if (!target.classList.contains('sr2-image-reveal')) target.classList.add('sr2-reveal');
      revealObserver.observe(target);
    });
  } else {
    revealTargets.forEach((target) => target.classList.add('is-seen'));
  }

  const setupPinnedWorld = (world, rail, chapters, previous, next, count, progress) => {
    const stage = world.querySelector('[data-scroll-world-stage]');
    if (!stage) return false;

    let start = 0;
    let distance = 1;
    let frame = 0;

    world.classList.add('is-scroll-world');
    rail.scrollLeft = 0;

    const setPosition = (ratio) => {
      const safeRatio = Math.min(1, Math.max(0, ratio));
      rail.style.transform = `translate3d(${-safeRatio * distance}px, 0, 0)`;
      if (progress) progress.style.transform = `scaleX(${1 + safeRatio * 3})`;
      if (count && chapters.length) {
        const current = Math.min(chapters.length - 1, Math.round(safeRatio * (chapters.length - 1)));
        count.textContent = `${String(current + 1).padStart(2, '0')} / ${String(chapters.length).padStart(2, '0')}`;
      }
    };

    const update = () => {
      setPosition((window.scrollY - start) / distance);
      frame = 0;
    };

    const requestUpdate = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(update);
    };

    const layout = () => {
      const headerHeight = Number.parseFloat(getComputedStyle(root).getPropertyValue('--sr2-header')) || 0;
      const worldTop = world.getBoundingClientRect().top + window.scrollY;
      distance = Math.max(1, rail.scrollWidth - stage.clientWidth);
      start = worldTop + stage.offsetTop - headerHeight;
      world.style.height = `${stage.offsetTop + stage.clientHeight + distance}px`;
      requestUpdate();
    };

    const goToChapter = (offset) => {
      const currentRatio = Math.min(1, Math.max(0, (window.scrollY - start) / distance));
      const current = Math.round(currentRatio * (chapters.length - 1));
      const target = Math.min(chapters.length - 1, Math.max(0, current + offset));
      const top = start + (target / Math.max(1, chapters.length - 1)) * distance;
      window.scrollTo({ top, behavior: reducedMotion ? 'auto' : 'smooth' });
    };

    previous?.addEventListener('click', () => goToChapter(-1));
    next?.addEventListener('click', () => goToChapter(1));
    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', () => window.requestAnimationFrame(layout), { passive: true });

    window.requestAnimationFrame(layout);
    return true;
  };

  const setupRail = (rail) => {
    const world = rail.closest('[data-horizontal-world]');
    const previous = world ? world.querySelector('[data-rail-prev]') : null;
    const next = world ? world.querySelector('[data-rail-next]') : null;
    const count = world ? world.querySelector('[data-rail-count]') : null;
    const progress = world ? world.querySelector('[data-rail-progress]') : null;
    const chapters = Array.from(rail.children);
    const storyProgress = rail.parentElement ? rail.parentElement.querySelector('.sr2-world-story__progress span') : null;

    if (world?.classList.contains('sr2-worlds') && finePointer && !reducedMotion && window.matchMedia('(min-width: 901px)').matches) {
      if (setupPinnedWorld(world, rail, chapters, previous, next, count, progress)) return;
    }

    const amount = () => {
      const first = chapters[0];
      return first ? first.getBoundingClientRect().width + 24 : rail.clientWidth * 0.8;
    };

    const updateRail = () => {
      const max = Math.max(1, rail.scrollWidth - rail.clientWidth);
      const ratio = Math.min(1, Math.max(0, rail.scrollLeft / max));
      if (progress) progress.style.transform = `scaleX(${1 + ratio * 3})`;
      if (storyProgress) storyProgress.style.transform = `scaleX(${ratio})`;

      if (count && chapters.length) {
        const center = rail.scrollLeft + rail.clientWidth / 2;
        let current = 0;
        chapters.forEach((chapter, index) => {
          if (chapter.offsetLeft <= center) current = index;
        });
        count.textContent = `${String(Math.min(current + 1, chapters.length)).padStart(2, '0')} / ${String(chapters.length).padStart(2, '0')}`;
      }
    };

    previous?.addEventListener('click', () => rail.scrollBy({ left: -amount(), behavior: reducedMotion ? 'auto' : 'smooth' }));
    next?.addEventListener('click', () => rail.scrollBy({ left: amount(), behavior: reducedMotion ? 'auto' : 'smooth' }));
    rail.addEventListener('scroll', () => window.requestAnimationFrame(updateRail), { passive: true });

    if (finePointer && !reducedMotion) {
      rail.addEventListener('wheel', (event) => {
        if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
        const max = rail.scrollWidth - rail.clientWidth;
        const movingForward = event.deltaY > 0;
        const canMove = movingForward ? rail.scrollLeft < max - 2 : rail.scrollLeft > 2;
        if (!canMove) return;
        event.preventDefault();
        rail.scrollLeft += event.deltaY;
      }, { passive: false });
    }

    updateRail();
  };

  document.querySelectorAll('[data-horizontal-rail]').forEach(setupRail);

  document.querySelectorAll('[data-interactive-scene]').forEach((scene) => {
    const hotspots = Array.from(scene.querySelectorAll('[data-scene-hotspot]'));
    const cards = Array.from(scene.querySelectorAll('[data-scene-card]'));
    const activate = (index) => {
      hotspots.forEach((item, itemIndex) => item.classList.toggle('is-active', itemIndex === index));
      cards.forEach((item, itemIndex) => item.classList.toggle('is-active', itemIndex === index));
    };
    hotspots.forEach((hotspot, index) => {
      hotspot.addEventListener('mouseenter', () => activate(index));
      hotspot.addEventListener('focus', () => activate(index));
    });
    cards.forEach((card, index) => {
      card.addEventListener('mouseenter', () => activate(index));
      card.addEventListener('focus', () => activate(index));
    });
  });

  if (finePointer && !reducedMotion) {
    document.querySelectorAll('[data-depth-card]').forEach((card) => {
      card.addEventListener('pointermove', (event) => {
        const bounds = card.getBoundingClientRect();
        const x = (event.clientX - bounds.left) / bounds.width - 0.5;
        const y = (event.clientY - bounds.top) / bounds.height - 0.5;
        card.style.transform = `perspective(900px) rotateX(${-y * 2.5}deg) rotateY(${x * 2.5}deg) translateY(-2px)`;
      });
      card.addEventListener('pointerleave', () => {
        card.style.transform = '';
      });
    });

    document.querySelectorAll('[data-hero-depth]').forEach((hero) => {
      const media = hero.querySelector('img');
      if (!media) return;
      hero.addEventListener('pointermove', (event) => {
        const x = event.clientX / window.innerWidth - 0.5;
        const y = event.clientY / window.innerHeight - 0.5;
        media.style.transform = `scale(1.025) translate(${x * -8}px, ${y * -6}px)`;
      });
      hero.addEventListener('pointerleave', () => {
        media.style.transform = '';
      });
    });
  }

  /* Cinematic hero video: custom fade loop, no CSS opacity transition. */
  const heroVideo = document.querySelector('[data-hero-video]');
  const heroNav = document.querySelector('.sr-home__hero-nav');
  if (heroVideo) {
    const FADE_MS = 500;
    let fadeFrame = 0;
    let fadeStart = 0;
    let fadeFrom = 0;
    let fadeTarget = 0;

    const fadeTo = (target) => {
      if (reducedMotion || saveData) {
        heroVideo.style.opacity = String(target);
        return;
      }
      fadeStart = performance.now();
      fadeFrom = Number.parseFloat(heroVideo.style.opacity || getComputedStyle(heroVideo).opacity) || 0;
      fadeTarget = target;
      if (fadeFrame) return;
      const tick = (now) => {
        const progress = Math.min(1, (now - fadeStart) / FADE_MS);
        const eased = 1 - ((1 - progress) ** 3);
        const lerped = fadeFrom + ((fadeTarget - fadeFrom) * eased);
        heroVideo.style.opacity = String(lerped);
        if (progress < 1) {
          fadeFrame = window.requestAnimationFrame(tick);
        } else {
          fadeFrame = 0;
        }
      };
      fadeFrame = window.requestAnimationFrame(tick);
    };

    if (reducedMotion || saveData) {
      heroVideo.pause();
      heroVideo.style.opacity = '1';
    } else {
      heroVideo.addEventListener('loadeddata', () => {
        heroVideo.play().then(() => fadeTo(1)).catch(() => {});
      }, { once: true });
      heroVideo.addEventListener('timeupdate', () => {
        if (Number.isFinite(heroVideo.duration) && heroVideo.duration - heroVideo.currentTime <= 0.55) fadeTo(0);
      });
      heroVideo.addEventListener('ended', () => {
        heroVideo.style.opacity = '0';
        heroVideo.currentTime = 0;
        window.setTimeout(() => heroVideo.play().then(() => fadeTo(1)).catch(() => {}), 100);
      });
      heroVideo.load();
    }
  }

  if (heroNav) {
    const updateHeroNav = () => heroNav.classList.toggle('is-scrolled', window.scrollY > 100);
    updateHeroNav();
    window.addEventListener('scroll', updateHeroNav, { passive: true });
  }

  const heroHeadline = document.querySelector('[data-hero-headline]');
  if (heroHeadline && !reducedMotion) {
    heroHeadline.innerHTML = heroHeadline.textContent.trim().split(/\s+/).map((word, index) => `<span class="sr-home__hero-word" style="--word-delay:${index * 100}ms">${word}</span>`).join(' ');
  }

  const bayMap = document.querySelector('[data-bay-map]');
  if (bayMap) {
    const stops = Array.from(bayMap.querySelectorAll('[data-bay-stop]'));
    const status = bayMap.querySelector('[data-bay-status]');
    const labels = {
      oakland: 'Oakland · The root',
      'san-francisco': 'San Francisco · The fog',
      'san-jose': 'San Jose · The night',
    };
    const lightStop = (stop, index) => {
      window.setTimeout(() => {
        stop.classList.add('is-lit');
        if (status) status.textContent = labels[stop.dataset.bayStop] || `Chapter ${index + 1}`;
      }, reducedMotion ? 0 : index * 650);
    };
    const lightAll = () => {
      bayMap.classList.add('is-active');
      stops.forEach(lightStop);
    };
    if (reducedMotion || !('IntersectionObserver' in window)) {
      lightAll();
    } else {
      const mapObserver = new IntersectionObserver((entries, observer) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        lightAll();
        observer.disconnect();
      }, { threshold: 0.35 });
      mapObserver.observe(bayMap);
    }
    stops.forEach((stop, index) => stop.addEventListener('focus', () => {
      stop.classList.add('is-lit');
      if (status) status.textContent = labels[stop.dataset.bayStop] || `Chapter ${index + 1}`;
    }));
  }
})();
