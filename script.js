const seoData = {
  '#home': {
    title: 'AI Literacy and Future-Ready Skills for K–12 Schools | TomoClub',
    description: 'TomoClub is the K–12 implementation partner for AI literacy and future-ready skills. Built, delivered, and supported for real classrooms, real teachers, and real students. 14+ US states and 10+ countries.'
  },
  '#ai-literacy': {
    title: 'AI Literacy Curriculum for Grades 6–12 | TomoClub',
    description: 'Standards-aligned AI literacy curriculum for middle and high school students. Two differentiated tracks. Aligned to AI4K12, ISTE, and UNESCO. Full teacher support included. Request a free pilot.'
  },
  '#future-ready': {
    title: 'Future-Ready Skills Program for K–12 Schools | TomoClub',
    description: 'Game-based learning program that builds communication, collaboration, leadership, and creative problem-solving in students from Grades 3–12. Built on CASEL framework. Measurable outcomes.'
  },
  '#pd': {
    title: 'AI Professional Development for Teachers | TomoClub',
    description: 'Practical, customized AI PD for K–12 educators. Builds teacher confidence with AI tools, classroom ethics, and academic integrity. Hands-on and ready to apply the next day.'
  },
  '#about': {
    title: 'About TomoClub | K–12 AI Literacy and Future-Ready EdTech',
    description: 'TomoClub is a mission-driven EdTech company serving 10,000+ students and 5,000+ teachers across 14+ US states and 10+ countries. The implementation partner for future-ready education.'
  },
  '#faqs': {
    title: 'FAQs | TomoClub AI Literacy and Future-Ready Skills Programs',
    description: 'Answers to the most common questions about TomoClub programs, pricing, implementation timelines, grade levels, teacher support, and funding options.'
  },
  '#ebook': {
    title: 'Leaders of Tomorrow | Free Ebook by 15 School Leaders | TomoClub',
    description: 'Download the free Leaders of Tomorrow ebook — 15 real school leaders share what it takes to lead future-ready schools in an AI world. 400+ combined years. Free during launch week.'
  },
  '#education-hall': {
    title: 'The Education Hall | TomoClub',
    description: 'Real Stories from Schools Rethinking Education. Explore fresh ideas, perspectives, and conversations on how education needs to evolve for today\'s learners.'
  },
  '#podcast': {
    title: 'The TomoClub Podcast | Play & Learn',
    description: 'Listen to discussions on SEL, AI literacy, school leadership, and preparing students for the 21st century. New episodes weekly.'
  },
  '#guides': {
    title: 'Guides & Toolkits for School Leaders | TomoClub',
    description: 'Download practical roadmaps, SEL toolkits, and activation guides for your school district. Built by practitioners for future-ready education.'
  },
  '#signup': {
    title: 'Get Started with TomoClub | Request a Pilot',
    description: 'Ready to bring future-ready skills to your school? Contact our team to design a pilot program for your district.'
  },
  '#blog': {
    title: 'TomoClub Blog | Insights on AI and Leadership in Education',
    description: 'Exploring the intersection of technology, leadership, and human-centered learning. Real stories and practical strategies for future-ready schools.'
  },
  'blog/why-schools-should-train-teachers-in-ai-literacy/': {
    title: 'Why Schools Should Train Teachers in AI Literacy | TomoClub Blog',
    description: 'Discover Why Schools Should Train Teachers in AI Literacy by Building Confidence, Reducing Workload, and Preparing Educators to Guide Students in a Tech-Driven Future'
  }
};

// Security Helper: Lightweight sanitization
function sanitizeHTML(html) {
  if (typeof DOMPurify !== 'undefined') {
    return DOMPurify.sanitize(html);
  }
  // Fallback if DOMPurify fails to load (removes script tags)
  return html.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gim, "");
}

document.addEventListener('DOMContentLoaded', () => {
  // ... existing code ...
  // --- 1. Routing & Visibility (Priority) ---
  const pages = document.querySelectorAll('.page');
  const navLinks = document.querySelectorAll('nav a[href^="#"]');

  function navigateFromHash() {
    try {
      let hash = window.location.hash || '#home';
      if(hash === '#') return;

      // Update SEO Data
      const currentSeo = seoData[hash] || seoData['#home'];
      const pageTitle = document.getElementById('page-title');
      const metaDesc = document.getElementById('meta-description');
      if (pageTitle && currentSeo.title) pageTitle.textContent = currentSeo.title;
      if (metaDesc && currentSeo.description) metaDesc.setAttribute('content', currentSeo.description);

      // Update Social Tags
      const ogTitle = document.getElementById('og-title');
      const ogDesc = document.getElementById('og-description');
      const ogUrl = document.getElementById('og-url');
      const twTitle = document.getElementById('tw-title');
      const twDesc = document.getElementById('tw-desc');
      const canonicalLink = document.getElementById('canonical-link');

      if (ogTitle) ogTitle.setAttribute('content', currentSeo.title);
      if (ogDesc) ogDesc.setAttribute('content', currentSeo.description);
      if (ogUrl && currentSeo.url) ogUrl.setAttribute('content', currentSeo.url);
      if (twTitle) twTitle.setAttribute('content', currentSeo.title);
      if (twDesc) twDesc.setAttribute('content', currentSeo.description);
      if (canonicalLink && currentSeo.url) canonicalLink.setAttribute('href', currentSeo.url);

      pages.forEach(page => {
        if ('#' + page.id === hash) {
          page.classList.add('active');
          setTimeout(() => page.classList.add('faded-in'), 10);
          
          const animatedElements = page.querySelectorAll('.animate-on-scroll');
          animatedElements.forEach(el => el.classList.remove('visible'));
          setTimeout(() => {
            if (typeof observeElements === 'function') observeElements();
          }, 100);
        } else {
          page.classList.remove('active');
          page.classList.remove('faded-in');
        }
      });

      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      console.error('Routing error:', e);
    }
  }

  window.addEventListener('hashchange', navigateFromHash);
  navigateFromHash();

  // --- 2. Initializations ---
  
  // Initial icon creation
  if (typeof lucide !== 'undefined') lucide.createIcons();

  // Announcement Banner Logic
  const banner = document.getElementById('announcement-banner');
  const closeBannerBtn = document.getElementById('close-banner');
  
  if (banner && closeBannerBtn) {
    const today = new Date();
    const startDate = new Date('2026-04-27T00:00:00');
    const endDate = new Date('2026-05-05T23:59:59');
    const isBannerDismissed = localStorage.getItem('bannerDismissed_Ebook') === 'true';

    if (today >= startDate && today <= endDate && !isBannerDismissed) {
      banner.style.display = 'block';
      document.body.classList.add('has-banner');
      if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    closeBannerBtn.addEventListener('click', () => {
      banner.style.display = 'none';
      document.body.classList.remove('has-banner');
      localStorage.setItem('bannerDismissed_Ebook', 'true');
    });
  }

  // TAICY Ticker Banner Logic
  const taicyBanner = document.getElementById('taicy-ticker-banner');
  const taicyTickerTrack = document.getElementById('taicy-ticker-track');

  if (taicyBanner && taicyTickerTrack) {
    const today = new Date();
    const startDate = new Date('2026-08-21T00:00:00');
    const endDate = new Date('2026-09-20T23:59:59');

    if (today >= startDate && today <= endDate) {
      taicyBanner.style.display = 'block';
      document.body.classList.add('has-taicy-banner');

      // The -50% loop animation is only seamless with an EVEN number of
      // identical copies. Duplicate the chunk up to the nearest even count
      // that covers 2x the viewport width, so there's never a gap on wide
      // screens, then set the animation duration so scroll speed stays
      // constant regardless of how many copies were needed.
      const chunk = taicyTickerTrack.firstElementChild;
      const chunkWidth = chunk.getBoundingClientRect().width;
      const targetWidth = window.innerWidth * 2;
      let copies = Math.max(2, Math.ceil(targetWidth / chunkWidth));
      if (copies % 2 !== 0) copies += 1;

      for (let i = 1; i < copies; i++) {
        taicyTickerTrack.appendChild(chunk.cloneNode(true));
      }

      const pxPerSecond = 70;
      const duration = (copies / 2) * chunkWidth / pxPerSecond;
      taicyTickerTrack.style.animationDuration = duration + 's';
    }
  }

  // Theme Toggle Logic
  const themeToggleBtn = document.getElementById('theme-toggle');
  if (themeToggleBtn) {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      document.body.classList.add('dark-theme');
    }

    const updateIcons = () => {
      const isDark = document.body.classList.contains('dark-theme');
      const moonIcons = document.querySelectorAll('.theme-icon-moon');
      const sunIcons = document.querySelectorAll('.theme-icon-sun');
      moonIcons.forEach(icon => icon.style.display = isDark ? 'none' : 'block');
      sunIcons.forEach(icon => icon.style.display = isDark ? 'block' : 'none');
    };
    updateIcons();

    themeToggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('dark-theme');
      localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
      updateIcons();
    });
  }

  // Navigation Background on Scroll
  const nav = document.querySelector('nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    });
  }

  // Mobile Menu Toggle
  const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
  const navLinksContainer = document.getElementById('nav-links');
  const menuIconOpen = document.getElementById('menu-icon-open');
  const menuIconClose = document.getElementById('menu-icon-close');

  if (mobileMenuToggle && navLinksContainer) {
    mobileMenuToggle.addEventListener('click', () => {
      const isActive = navLinksContainer.classList.toggle('active');
      if (menuIconOpen && menuIconClose) {
        menuIconOpen.style.display = isActive ? 'none' : 'block';
        menuIconClose.style.display = isActive ? 'block' : 'none';
      }
    });

    const links = navLinksContainer.querySelectorAll('a');
    links.forEach(link => {
      link.addEventListener('click', () => {
        navLinksContainer.classList.remove('active');
        if (menuIconOpen && menuIconClose) {
          menuIconOpen.style.display = 'block';
          menuIconClose.style.display = 'none';
        }
      });
    });
  }

  // Mobile Dropdown Toggle (Centralized)
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    const link = item.querySelector('a');
    const dropdown = item.querySelector('.dropdown');
    if (link && dropdown) {
      link.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          const isOpen = dropdown.style.maxHeight === '500px';
          dropdown.style.maxHeight = isOpen ? '0' : '500px';
          const icon = link.querySelector('i');
          if (icon) icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
        }
      });
    }
  });

  // Intersection Observer for scroll animations
  function observeElements() {
    let delayCounter = 0;
    let timeout;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = `${delayCounter * 120}ms`;
          entry.target.classList.add('visible');
          delayCounter++; 
          clearTimeout(timeout);
          timeout = setTimeout(() => { delayCounter = 0; }, 100);
          setTimeout(() => { entry.target.style.transitionDelay = '0ms'; }, 1500 + (delayCounter * 120));
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -60px 0px" });

    document.querySelectorAll('.animate-on-scroll:not(.visible)').forEach(el => {
      observer.observe(el);
    });
  }
  observeElements();

  // FAQ Accordion Logic
  document.querySelectorAll('.faq-question').forEach(question => {
    question.addEventListener('click', () => {
      const item = question.parentElement;
      const isActive = item.classList.contains('active');
      
      // Close all other FAQ items
      document.querySelectorAll('.faq-item').forEach(otherItem => {
        if (otherItem !== item) {
          otherItem.classList.remove('active');
        }
      });
      
      // Toggle current item
      item.classList.toggle('active');
    });
  });

  // Team Card Flip Listener
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.team-card');
    if (card) {
      if (e.target.closest('.team-social-links')) return;
      card.classList.toggle('flipped');
      document.querySelectorAll('.team-card.flipped').forEach(otherCard => {
        if (otherCard !== card) otherCard.classList.remove('flipped');
      });
    } else if (!e.target.closest('.team-container')) {
      document.querySelectorAll('.team-card.flipped').forEach(card => card.classList.remove('flipped'));
    }
  });

  // Counter Animation
  const statsSection = document.querySelector('.stats-grid');
  if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        document.querySelectorAll('.counter').forEach(counter => {
          const target = +counter.getAttribute('data-target');
          const countElement = counter.querySelector('.count');
          let current = 0;
          const increment = target / 50;
          const updateCount = () => {
            if (current < target) {
              current += increment;
              countElement.innerText = Math.ceil(current);
              setTimeout(updateCount, 20);
            } else {
              countElement.innerText = target;
            }
          };
          updateCount();
        });
        observer.unobserve(statsSection);
      }
    }, { threshold: 0.1 });
    observer.observe(statsSection);
  }

  // Form Handling
  const mainSignupForm = document.getElementById('signup-form');
  const signupSuccessView = document.getElementById('signup-success');
  if (mainSignupForm) {
    mainSignupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = mainSignupForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Sending...';

        try {
        const formData = new FormData(mainSignupForm);
        const data = Object.fromEntries(formData.entries());
        data.type = 'signup';
        
        await fetch('/api/signup', { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        mainSignupForm.style.display = 'none';
        if (signupSuccessView) signupSuccessView.style.display = 'block';
        if (typeof lucide !== 'undefined') lucide.createIcons();
      } catch (err) {
        console.error('Signup error:', err);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // Home Newsletter Form
  const homeNewsletterForm = document.getElementById('home-newsletter-form');
  const homeNewsletterSuccess = document.getElementById('home-newsletter-success');
  if (homeNewsletterForm) {
    homeNewsletterForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = homeNewsletterForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.disabled = true;
      submitBtn.innerHTML = 'Joining...';

      try {
        const formData = new FormData(homeNewsletterForm);
        const data = Object.fromEntries(formData.entries());
        data.type = 'newsletter';
        data.source = 'Homepage Newsletter Section';
        
        await fetch('/api/signup', { 
          method: 'POST', 
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        homeNewsletterForm.style.display = 'none';
        if (homeNewsletterSuccess) homeNewsletterSuccess.style.display = 'block';
        if (typeof lucide !== 'undefined') lucide.createIcons();
      } catch (err) {
        console.error('Newsletter error:', err);
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  }

  // --- Download Modal Logic ---
  const downloadModal = document.getElementById('download-modal');
  const downloadButtons = document.querySelectorAll('.open-download-modal');
  const closeDownloadBtn = document.getElementById('close-download-btn');
  const toolkitForm = document.getElementById('toolkit-download-form');
  const successMsg = document.getElementById('download-success-msg');
  const manualDownloadLink = document.getElementById('manual-download-link');
  const modalTitle = document.getElementById('modal-download-title');
  const formToolkitName = document.getElementById('form-toolkit-name');

  if (downloadModal && downloadButtons.length > 0) {
    downloadButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const fileName = btn.getAttribute('data-file');
        const title = btn.getAttribute('data-title');
        
        if (modalTitle) modalTitle.textContent = title;
        if (formToolkitName) formToolkitName.value = title;
        
        // Store filename for download
        downloadModal.setAttribute('data-current-file', fileName);
        
        downloadModal.classList.add('active');
        if (toolkitForm) toolkitForm.style.display = 'block';
        if (successMsg) successMsg.style.display = 'none';
      });
    });

    if (closeDownloadBtn) {
      closeDownloadBtn.addEventListener('click', () => {
        downloadModal.classList.remove('active');
      });
    }

    downloadModal.addEventListener('click', (e) => {
      if (e.target === downloadModal) {
        downloadModal.classList.remove('active');
      }
    });

    if (toolkitForm) {
      toolkitForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = toolkitForm.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : 'Get My Guide';
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = 'Preparing download...';
        }

        try {
          const formData = new FormData(toolkitForm);
          const data = Object.fromEntries(formData.entries());
          data.type = 'resource';
          data.toolkitName = downloadModal.getAttribute('data-current-file'); // Re-ensure toolkit name

          // Send to secure proxy
          await fetch('/api/signup', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          
          const fileName = downloadModal.getAttribute('data-current-file');
          const downloadUrl = fileName.includes('/') ? fileName : `toolkits/${fileName}`;
          
          // Show success message
          toolkitForm.style.display = 'none';
          if (successMsg) successMsg.style.display = 'block';
          if (manualDownloadLink) {
            manualDownloadLink.href = downloadUrl;
            manualDownloadLink.setAttribute('download', fileName);
          }
          
          // Trigger automatic download
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = fileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          if (typeof lucide !== 'undefined') lucide.createIcons();
        } catch (err) {
          console.error('Download form error:', err);
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
          }
        }
      });
    }
  }

  // --- Pilot Modal Logic ---
  const pilotModal = document.getElementById('pilot-modal');
  const openPilotBtns = document.querySelectorAll('.open-pilot-modal');
  const closePilotBtn = document.getElementById('close-pilot-btn');
  const pilotIframe = document.getElementById('pilot-iframe');
  const pilotFormUrl = 'https://91fabf1c.sibforms.com/v2/serve/MUIFAKeejaVgAe6G18ijnd1U-_b-q5wwqWzAAdp-46T-FSh3yStr_6qw8aeR19UjV40KMRWBGFQErR3NuMTCAmG_-KUhUOYxLU6-Nzza27KOqv33BSKj1pi2yF5sKpquz-KXLYHY8-nnSxH1lt1wkx9dy6n9Yag5Bllp8Grh6x6YnVdT-wVhFN1pgUpqf2R0tY7UuCdnEPrMWXJEiA==';

  if (pilotModal && openPilotBtns.length > 0) {
    openPilotBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        pilotModal.classList.add('active');
        
        // Reset form if success message is visible
        const formContainer = document.getElementById('pilot-form-container');
        const successMsg = document.getElementById('pilot-success-msg');
        if (formContainer && successMsg) {
          formContainer.style.display = 'block';
          successMsg.style.display = 'none';
        }
      });
    });

    if (closePilotBtn) {
      closePilotBtn.addEventListener('click', () => {
        pilotModal.classList.remove('active');
      });
    }

    pilotModal.addEventListener('click', (e) => {
      if (e.target === pilotModal) {
        pilotModal.classList.remove('active');
      }
    });

    // Form Submission Handling
    const pilotForm = document.getElementById('pilot-signup-form');
    if (pilotForm) {
      pilotForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = pilotForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Sending...';

        try {
          const formData = new FormData(pilotForm);
          const data = Object.fromEntries(formData.entries());
          data.type = 'pilot'; // Or 'signup' if you prefer unified

          await fetch('/api/signup', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          
          const formContainer = document.getElementById('pilot-form-container');
          const successMsg = document.getElementById('pilot-success-msg');
          if (formContainer) formContainer.style.display = 'none';
          if (successMsg) successMsg.style.display = 'block';
          if (typeof lucide !== 'undefined') lucide.createIcons();
        } catch (err) {
          console.error('Pilot signup error:', err);
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
      });
    }
  }

  // --- Article Filtering (Educational Hall) ---
  const articleSearch = document.getElementById('article-search');
  const articleFilter = document.getElementById('article-filter');
  const articlesGrid = document.getElementById('articles-grid');

  if (articleSearch && articleFilter && articlesGrid) {
    const articles = Array.from(articlesGrid.children);
    articles.forEach((article, index) => {
      article.setAttribute('data-timestamp', index + 1);
    });

    function filterArticles() {
      const query = articleSearch.value.toLowerCase();
      const sortOrder = articleFilter.value;
      
      let visibleArticles = [];

      articles.forEach(article => {
        const titleEl = article.querySelector('.article-title');
        const title = titleEl ? titleEl.textContent.toLowerCase() : '';
        
        if (title.includes(query)) {
          article.style.display = 'block';
          visibleArticles.push(article);
        } else {
          article.style.display = 'none';
        }
      });

      visibleArticles.sort((a, b) => {
        const timeA = parseInt(a.getAttribute('data-timestamp'));
        const timeB = parseInt(b.getAttribute('data-timestamp'));
        return sortOrder === 'latest' ? timeB - timeA : timeA - timeB;
      });

      visibleArticles.forEach(article => articlesGrid.appendChild(article));
    }

    articleSearch.addEventListener('input', filterArticles);
    articleFilter.addEventListener('change', filterArticles);
    filterArticles();
  }

  // --- Podcast Filtering ---
  const podcastSearch = document.getElementById('podcast-search');
  const podcastFilter = document.getElementById('podcast-filter');
  const podcastGrid = document.getElementById('podcast-grid');

  if (podcastSearch && podcastFilter && podcastGrid) {
    const podcasts = Array.from(podcastGrid.children);

    function filterPodcasts() {
      const query = podcastSearch.value.toLowerCase();
      const sortOrder = podcastFilter.value;

      let visiblePodcasts = [];

      podcasts.forEach(podcast => {
        const titleEl = podcast.querySelector('h3');
        const speakerEl = podcast.querySelector('p');
        const title = titleEl ? titleEl.textContent.toLowerCase() : '';
        const speaker = speakerEl ? speakerEl.textContent.toLowerCase() : '';
        
        if (title.includes(query) || speaker.includes(query)) {
          podcast.style.display = '';
          visiblePodcasts.push(podcast);
        } else {
          podcast.style.display = 'none';
        }
      });

      visiblePodcasts.sort((a, b) => {
        const timeA = parseInt(a.getAttribute('data-timestamp') || 0);
        const timeB = parseInt(b.getAttribute('data-timestamp') || 0);
        return sortOrder === 'latest' ? timeB - timeA : timeA - timeB;
      });

      visiblePodcasts.forEach(podcast => podcastGrid.appendChild(podcast));
    }

    podcastSearch.addEventListener('input', filterPodcasts);
    podcastFilter.addEventListener('change', filterPodcasts);
    filterPodcasts();
  }
});
