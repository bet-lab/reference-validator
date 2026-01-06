/* Custom JavaScript for BibTeX Validator Documentation
 * Initializes Lucide Icons and provides interactive features
 */

(function() {
    'use strict';

    // Initialize Lucide Icons when DOM is ready
    function initLucideIcons() {
        if (typeof lucide !== 'undefined') {
            // Initialize all icons in the document
            lucide.createIcons();
            
            // Re-initialize icons after dynamic content loads
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        // Check if any added nodes contain icon elements
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1) { // Element node
                                if (node.querySelector && node.querySelector('[data-lucide]')) {
                                    lucide.createIcons({ root: node });
                                }
                            }
                        });
                    }
                });
            });

            // Observe the document body for changes
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        } else {
            console.warn('Lucide Icons library not loaded. Icons may not display correctly.');
        }
    }

    // Dark mode toggle integration with Shibuya theme
    function initDarkModeToggle() {
        // Check if Shibuya theme has dark mode toggle
        const themeToggle = document.querySelector('[data-theme-toggle]') || 
                           document.querySelector('.theme-toggle') ||
                           document.querySelector('button[aria-label*="theme" i]');
        
        if (themeToggle) {
            themeToggle.addEventListener('click', function() {
                // Update CSS variables when theme changes
                setTimeout(function() {
                    updateThemeVariables();
                }, 100);
            });
        }

        // Listen for theme changes via media query
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addEventListener('change', function(e) {
            updateThemeVariables();
        });
    }

    // Update CSS variables based on current theme
    function updateThemeVariables() {
        const isDark = document.documentElement.classList.contains('dark') ||
                      document.documentElement.getAttribute('data-theme') === 'dark' ||
                      window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (isDark) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }

    // Enhanced code block copy functionality
    function enhanceCodeBlocks() {
        // This works with sphinx-copybutton, but we can add additional enhancements
        const codeBlocks = document.querySelectorAll('pre code, .highlight');
        
        codeBlocks.forEach(function(block) {
            // Add hover effect
            block.addEventListener('mouseenter', function() {
                this.style.transition = 'background-color 0.2s';
            });
        });
    }

    // Smooth scroll for anchor links
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href.length > 1) {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }

    // Initialize tooltips for elements with title attribute
    function initTooltips() {
        const elementsWithTitle = document.querySelectorAll('[title]');
        elementsWithTitle.forEach(function(element) {
            element.addEventListener('mouseenter', function() {
                // Add custom tooltip styling if needed
                this.style.cursor = 'help';
            });
        });
    }

    // Initialize everything when DOM is ready
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initLucideIcons();
                initDarkModeToggle();
                enhanceCodeBlocks();
                initSmoothScroll();
                initTooltips();
                updateThemeVariables();
            });
        } else {
            // DOM already loaded
            initLucideIcons();
            initDarkModeToggle();
            enhanceCodeBlocks();
            initSmoothScroll();
            initTooltips();
            updateThemeVariables();
        }
    }

    // Start initialization
    init();

    // Export functions for potential external use
    window.bibtexValidatorDocs = {
        initLucideIcons: initLucideIcons,
        updateThemeVariables: updateThemeVariables
    };
})();

