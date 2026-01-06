/**
 * SkyyRose Header Behavior
 * Handles scroll-based header transitions and logo color switching
 */

(function() {
  'use strict';

  // Header scroll behavior
  document.addEventListener('DOMContentLoaded', function() {
    const header = document.getElementById('site-header');
    
    if (!header) return;

    let lastScroll = 0;
    
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;
      
      // Add scrolled class after 50px
      if (currentScroll > 50) {
        header.classList.add('site-header--scrolled');
        header.classList.remove('site-header--transparent');
      } else {
        header.classList.remove('site-header--scrolled');
        header.classList.add('site-header--transparent');
      }
      
      lastScroll = currentScroll;
    });
  });

  /**
   * Change logo color based on page/section
   * 
   * @param {string} variant - Logo color variant (gold, silver, rose-gold, deep-rose, black)
   */
  window.updateLogoColor = function(variant) {
    const logo = document.querySelector('.skyyrose-logo');
    if (!logo) return;
    
    // Remove all variant classes
    logo.className = 'skyyrose-logo';
    
    // Add new variant class
    logo.classList.add('skyyrose-logo--' + variant);
  };

  /**
   * Automatically update logo color based on page type
   */
  function autoUpdateLogoColor() {
    const body = document.body;
    
    if (body.classList.contains('collection-signature')) {
      updateLogoColor('rose-gold');
    } else if (body.classList.contains('collection-blackrose') || body.classList.contains('collection-black-rose')) {
      updateLogoColor('silver');
    } else if (body.classList.contains('collection-lovehurts') || body.classList.contains('collection-love-hurts')) {
      updateLogoColor('deep-rose');
    } else if (body.classList.contains('home')) {
      updateLogoColor('gold');
    }
  }

  // Run auto-update on load
  document.addEventListener('DOMContentLoaded', autoUpdateLogoColor);

  /**
   * Mobile menu toggle (if needed)
   */
  document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.site-header__hamburger');
    const nav = document.querySelector('.site-header__nav');
    
    if (!hamburger || !nav) return;

    hamburger.addEventListener('click', function() {
      this.classList.toggle('active');
      nav.classList.toggle('active');
    });
  });

})();