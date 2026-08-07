(() => {
  const button = document.querySelector('[data-srs-menu]');
  const nav = document.querySelector('#srs-nav');
  if (button && nav) button.addEventListener('click', () => { const open = nav.classList.toggle('is-open'); button.setAttribute('aria-expanded', String(open)); });

  const config = window.SKYY_SCROLL_WORLD_CONFIG;
  if (!config || !config.sections) return;
  const applyCollectionFonts = () => document.querySelectorAll('.sw-copy__title').forEach((title, index) => {
    const section = config.sections[index];
    if (section && section.font) title.style.fontFamily = `'${section.font}', cursive`;
  });
  new MutationObserver(applyCollectionFonts).observe(document.body, { childList: true, subtree: true });
  applyCollectionFonts();
})();
