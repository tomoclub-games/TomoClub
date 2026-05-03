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
  }
};

const SIGNUP_WEBHOOK = 'https://script.google.com/macros/s/AKfycbzz2VpoSdbCDsfGo4-3O6KnnjsEHUaMHuCCUN0KsQyBatGz_EMc-xdFC5FnvlKBWb40/exec';
const RESOURCE_WEBHOOK = 'https://script.google.com/macros/s/AKfycbwFuKr-0GwdBfPylk7pmIhcbQX401Qye5t61ZsrjfbQ6TUToblKfX-l2bzv5DAFKuxc/exec';

document.addEventListener('DOMContentLoaded', () => {
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
    }, { threshold: 0.5 });
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
        await fetch(SIGNUP_WEBHOOK, { method: 'POST', mode: 'no-cors', body: formData });
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
});
