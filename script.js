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
  // Announcement Banner Logic
  const banner = document.getElementById('announcement-banner');
  const closeBannerBtn = document.getElementById('close-banner');
  
  if (banner && closeBannerBtn) {
    const today = new Date();
    // Setting dates for 2026 as per user requirement
    const startDate = new Date('2026-04-27T00:00:00');
    const endDate = new Date('2026-05-05T23:59:59');
    const isBannerDismissed = localStorage.getItem('bannerDismissed_Ebook') === 'true';

    if (today >= startDate && today <= endDate && !isBannerDismissed) {
      banner.style.display = 'block';
      document.body.classList.add('has-banner');
      // Ensure icons are created for the banner
      if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    
    }

    closeBannerBtn.addEventListener('click', () => {
      banner.style.display = 'none';
      document.body.classList.remove('has-banner');
      localStorage.setItem('bannerDismissed_Ebook', 'true');
    });
  }

  // Navigation Background on Scroll
  const nav = document.querySelector('nav');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  });

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

    // Close menu when clicking a link
    const navLinks = navLinksContainer.querySelectorAll('a');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        navLinksContainer.classList.remove('active');
        if (menuIconOpen && menuIconClose) {
          menuIconOpen.style.display = 'block';
          menuIconClose.style.display = 'none';
        }
      });
    });
  }

  // Simple Hash Router & SEO Updater
  const pages = document.querySelectorAll('.page');
  const navLinks = document.querySelectorAll('nav a[href^="#"]');

  function navigateFromHash() {
    let hash = window.location.hash || '#home';
    if(hash === '#') return; // Don't navigate if it's just a dummy hash for a click event

    // Update SEO Data dynamically for SPA routing
    const currentSeo = seoData[hash] || seoData['#home'];
    document.getElementById('page-title').textContent = currentSeo.title;
    document.getElementById('meta-desc').setAttribute('content', currentSeo.description);

    // Update Social Tags
    const ogTitle = document.getElementById('og-title');
    const ogDesc = document.getElementById('og-desc');
    const twTitle = document.getElementById('tw-title');
    const twDesc = document.getElementById('tw-desc');

    if (ogTitle) ogTitle.setAttribute('content', currentSeo.title);
    if (ogDesc) ogDesc.setAttribute('content', currentSeo.description);
    if (twTitle) twTitle.setAttribute('content', currentSeo.title);
    if (twDesc) twDesc.setAttribute('content', currentSeo.description);

    pages.forEach(page => {
      if ('#' + page.id === hash) {
        page.classList.add('active');
        // Small delay to allow display:block to apply before animating opacity
        setTimeout(() => page.classList.add('faded-in'), 10);
        
        // trigger re-animation for elements inside the page
        const animatedElements = page.querySelectorAll('.animate-on-scroll');
        animatedElements.forEach(el => el.classList.remove('visible'));
        setTimeout(() => {
          observeElements();
        }, 100);
      } else {
        page.classList.remove('active');
        page.classList.remove('faded-in');
      }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  window.addEventListener('hashchange', navigateFromHash);
  
  // Initial load
  navigateFromHash();

  // Highlight active nav item
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const targetHash = link.getAttribute('href');
      // only intercept internal links
      if (targetHash.startsWith('#')) {
        navLinks.forEach(l => l.parentElement.classList.remove('active'));
        // Find closest .nav-item and mark active
        if(link.closest('.nav-item')) {
          link.closest('.nav-item').classList.add('active');
        }
      }
    });
  });

  // Intersection Observer for scroll animations with Staggering
  function observeElements() {
    let delayCounter = 0;
    let timeout;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Add a dynamic stagger delay for items appearing together
          entry.target.style.transitionDelay = `${delayCounter * 120}ms`;
          entry.target.classList.add('visible');
          
          delayCounter++; // increment delay for the next item in this batch
          
          // Clear previous timeout and set a new one to reset the counter
          // This groups almost-simultaneous intersections into a single stagger batch
          clearTimeout(timeout);
          timeout = setTimeout(() => {
            delayCounter = 0;
          }, 100);
          
          // Clean up the transition delay after it plays so hovers don't feel lagged
          setTimeout(() => {
            entry.target.style.transitionDelay = '0ms';
          }, 1500 + (delayCounter * 120));
          
          observer.unobserve(entry.target); // only animate once for maximum sleekness
        }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -60px 0px" });

    document.querySelectorAll('.animate-on-scroll:not(.visible)').forEach(el => {
      observer.observe(el);
    });
  }

  // Team Card Flip Listener
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.team-card');
    if (card) {
      card.classList.toggle('flipped');
    }
  });

  observeElements();

  // FAQ Accordion
  const faqItems = document.querySelectorAll('.faq-item');
  faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    question.addEventListener('click', () => {
      const isActive = item.classList.contains('active');
      faqItems.forEach(i => i.classList.remove('active'));
      if (!isActive) {
        item.classList.add('active');
      }
    });
  });

  // Ebook modal logic has been moved to the dedicated landing page
  // Counter Animation (Peak-End Staggered)
  let counterStaggerDelay = 0;
  let staggerTimeout;
  
  const animateCounters = (entries) => {
    entries.forEach(entry => {
      const counterElement = entry.target;
      const countSpan = counterElement.querySelector('.count');
      const target = +counterElement.getAttribute('data-target');

      if (entry.isIntersecting) {
        counterElement.dataset.animating = "true";
        countSpan.innerText = '0'; // Always start from 0
        
        // Stagger the start time of each counter
        setTimeout(() => {
          const updateCount = () => {
            if (counterElement.dataset.animating !== "true") return; // abort if scrolled away

            const count = +countSpan.innerText;
            const diff = target - count;
            
            if (diff > 0) {
              // Speedometer ease-out: move by 15% of remaining, at least 1
              const inc = Math.max(1, Math.ceil(diff * 0.15));
              countSpan.innerText = count + inc;
              setTimeout(updateCount, 30);
            } else {
              countSpan.innerText = target;
            }
          };
          updateCount();
        }, counterStaggerDelay);
        
        counterStaggerDelay += 250; // stagger next counter by 250ms
        
        clearTimeout(staggerTimeout);
        staggerTimeout = setTimeout(() => {
          counterStaggerDelay = 0;
        }, 1000);
        
      } else {
        // Reset when out of view so it animates again when scrolled to
        counterElement.dataset.animating = "false";
        countSpan.innerText = '0';
        counterStaggerDelay = 0;
      }
    });
  };

  const counterObserver = new IntersectionObserver(animateCounters, {
    root: null,
    threshold: 0.1
  });

  document.querySelectorAll('.counter').forEach(counter => {
    counterObserver.observe(counter);
  });

  // Article Modal Logic
  const articleModal = document.getElementById('article-modal');
  const closeArticleBtn = document.getElementById('close-article-btn');
  const articleModalTitle = document.getElementById('article-modal-title');
  const articleModalDate = document.getElementById('article-modal-date');
  const articleModalBody = document.getElementById('article-modal-body');

  if (articleModal) {
    document.querySelectorAll('.read-article-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const articleId = btn.getAttribute('data-article-id');
        const titleElement = btn.querySelector('.article-title');
        const dateElement = btn.querySelector('span'); // first span is the date
        
        if (articleId && typeof articlesData !== 'undefined' && articlesData[articleId]) {
          articleModalTitle.innerText = titleElement.innerText;
          articleModalDate.innerText = dateElement.innerText;
          articleModalBody.innerHTML = articlesData[articleId];
          articleModal.classList.add('active');
        }
      });
    });

    closeArticleBtn.addEventListener('click', () => {
      articleModal.classList.remove('active');
    });

    articleModal.addEventListener('click', (e) => {
      if (e.target === articleModal) {
        articleModal.classList.remove('active');
      }
    });
  }

  // Video Modal Logic
  const videoModal = document.getElementById('video-modal');
  const videoIframe = document.getElementById('video-iframe');
  const closeVideoModalBtn = document.getElementById('close-modal');
  
  if (videoModal && videoIframe && closeVideoModalBtn) {
    document.querySelectorAll('.play-video').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const videoId = btn.getAttribute('data-video-id');
        if (videoId) {
          const origin = window.location.origin || [window.location.protocol, '//', window.location.host].join('');
          videoIframe.src = `https://www.youtube-nocookie.com/embed/${videoId.trim()}?autoplay=1&rel=0&enablejsapi=1&origin=${encodeURIComponent(origin)}`;
          videoModal.style.display = 'flex';
        }
      });
    });

    closeVideoModalBtn.addEventListener('click', () => {
      videoModal.style.display = 'none';
      videoIframe.src = ''; // Stop video
    });

    videoModal.addEventListener('click', (e) => {
      if (e.target === videoModal) {
        videoModal.style.display = 'none';
        videoIframe.src = ''; // Stop video
      }
    });
  }

  // Podcast Search, Filter and Progressive Disclosure
  const podcastSearch = document.getElementById('podcast-search');
  const podcastFilter = document.getElementById('podcast-filter');
  const podcastGrid = document.getElementById('podcast-grid');
  
  if (podcastGrid) {
    const allPodcastCards = Array.from(podcastGrid.querySelectorAll('.podcast-card'));
    let currentlyVisibleCount = 12;
    
    // Create Load More Button
    const btnContainer = document.createElement('div');
    btnContainer.style.textAlign = 'center';
    btnContainer.style.marginTop = '2rem';
    btnContainer.style.gridColumn = '1 / -1';
    btnContainer.className = 'podcast-load-more-container';
    
    const loadMoreBtn = document.createElement('button');
    loadMoreBtn.className = 'btn btn-secondary';
    loadMoreBtn.innerHTML = 'Load More Episodes <i data-lucide="chevron-down"></i>';
    btnContainer.appendChild(loadMoreBtn);
    
    const updatePodcasts = () => {
      const searchTerm = podcastSearch ? podcastSearch.value.toLowerCase() : '';
      const sortOrder = podcastFilter ? podcastFilter.value : 'latest';
      
      let filteredCards = allPodcastCards.filter(card => {
        const text = card.textContent.toLowerCase();
        return text.includes(searchTerm);
      });
      
      filteredCards.sort((a, b) => {
        const numA = parseInt(a.getAttribute('data-timestamp') || 0, 10);
        const numB = parseInt(b.getAttribute('data-timestamp') || 0, 10);
        return sortOrder === 'latest' ? numB - numA : numA - numB;
      });
      
      // Clear grid
      allPodcastCards.forEach(card => {
        card.style.setProperty('display', 'none', 'important');
      });
      if (btnContainer.parentNode) {
        btnContainer.parentNode.removeChild(btnContainer);
      }
      
      // Append in sorted order
      filteredCards.forEach(card => podcastGrid.appendChild(card));
      
      // Show up to currentlyVisibleCount
      filteredCards.forEach((card, index) => {
        if (index < currentlyVisibleCount) {
          card.style.setProperty('display', 'flex', 'important');
        }
      });
      
      // Add Load More button if needed
      if (filteredCards.length > currentlyVisibleCount) {
        podcastGrid.appendChild(btnContainer);
        if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    
      }
    };
    
    // Initialize
    if (podcastFilter) podcastFilter.value = 'latest'; // Default to latest
    updatePodcasts();
    
    // Event Listeners
    if (podcastSearch) {
      podcastSearch.addEventListener('input', () => {
        currentlyVisibleCount = 12; // reset count on search
        updatePodcasts();
      });
    }
    
    if (podcastFilter) {
      podcastFilter.addEventListener('change', () => {
        currentlyVisibleCount = 12; // reset count on sort
        updatePodcasts();
      });
    }
    
    loadMoreBtn.addEventListener('click', () => {
      currentlyVisibleCount += 12;
      updatePodcasts();
    });
  }

  // Force navigation for Podcast Cards (Reliability Fix)
  document.addEventListener('click', (e) => {
    const card = e.target.closest('.podcast-card');
    if (card) {
      // If it has target="_blank", let the browser handle it
      if (card.getAttribute('target') === '_blank') return;
      
      const href = card.getAttribute('href');
      if (href && href.includes('podcast-player.html')) {
        e.preventDefault();
        window.location.href = href;
      }
    }
  }, true); // Use capture phase

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

    // Give lucide a small delay to finish SVG swap before updating icons
    setTimeout(updateIcons, 50);

    themeToggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      document.body.classList.toggle('dark-theme');
      const isDark = document.body.classList.contains('dark-theme');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
      updateIcons();
    });
  }

  // Contextual Floating CTA
  const floatingCta = document.getElementById('floating-cta');
  const heroSection = document.querySelector('.hero');
  
  if (floatingCta && heroSection) {
    window.addEventListener('scroll', () => {
      // Show only after scrolling completely past the hero section
      if (window.scrollY > (heroSection.offsetHeight * 1.2)) {
        floatingCta.classList.add('visible');
      } else {
        floatingCta.classList.remove('visible');
      }
    });
  }

  // Toolkit Download Modal Logic
  const downloadModal = document.getElementById('download-modal');
  const toolkitForm = document.getElementById('toolkit-download-form');
  const closeDownloadBtn = document.getElementById('close-download-btn');
  const downloadSuccessMsg = document.getElementById('download-success-msg');
  const manualDownloadLink = document.getElementById('manual-download-link');

  if (downloadModal) {
    // Open modal
    document.querySelectorAll('.open-download-modal').forEach(btn => {
      btn.addEventListener('click', () => {
        const fileName = btn.getAttribute('data-file');
        const toolkitName = btn.getAttribute('data-title');
        
        document.getElementById('form-file-name').value = fileName;
        document.getElementById('form-toolkit-name').value = toolkitName;
        document.getElementById('modal-download-title').innerText = `Download: ${toolkitName}`;
        
        // Reset form and view
        toolkitForm.style.display = 'block';
        downloadSuccessMsg.style.display = 'none';
        downloadModal.classList.add('active');
      });
    });

    // Close modal
    const closeModal = () => {
      downloadModal.classList.remove('active');
    };

    closeDownloadBtn.addEventListener('click', closeModal);
    downloadModal.addEventListener('click', (e) => {
      if (e.target === downloadModal) closeModal();
    });

    // Form Submission
    if (toolkitForm) {
      toolkitForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(toolkitForm);
        const fileName = formData.get('fileName');
        const submitBtn = toolkitForm.querySelector('button');
        const originalText = submitBtn.innerHTML;

        submitBtn.innerHTML = 'Sending... <i data-lucide="loader" class="spin"></i>';
        submitBtn.disabled = true;
        if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    

        try {
          // 1. Submit to Google Sheets (Resources/Old Sheet)
          await fetch(RESOURCE_WEBHOOK, {
            method: 'POST',
            mode: 'no-cors',
            body: formData
          });

          // 2. Submit to Brevo (Automated Email Delivery)
          // NOTE: For security, it's recommended to move this to a serverless function
          const email = formData.get('email');
          const firstName = formData.get('firstName') || 'Reader';
          const BREVO_API_KEY = 'YOUR_BREVO_API_KEY'; // REPLACE WITH YOUR API KEY
          const BREVO_LIST_ID = 3; // REPLACE WITH YOUR BREVO LIST ID (e.g., Toolkits list)

          if (BREVO_API_KEY !== 'YOUR_BREVO_API_KEY') {
              await fetch('https://api.brevo.com/v3/contacts', {
                  method: 'POST',
                  headers: {
                      'accept': 'application/json',
                      'api-key': BREVO_API_KEY,
                      'content-type': 'application/json'
                  },
                  body: JSON.stringify({
                      email: email,
                      attributes: { FIRSTNAME: firstName },
                      listIds: [BREVO_LIST_ID],
                      updateEnabled: true
                  })
              });
          }

          // Show success view
          toolkitForm.style.display = 'none';
          downloadSuccessMsg.style.display = 'block';
          
          const fileUrl = `./toolkits/${fileName}`;
          manualDownloadLink.href = fileUrl;

          // Trigger download
          const link = document.createElement('a');
          link.href = fileUrl;
          link.download = fileName;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);

        } catch (error) {
          console.error('Submission error:', error);
          alert('Something went wrong. Please try again.');
          submitBtn.innerHTML = originalText;
          submitBtn.disabled = false;
        }
      });
    }
  }

  // Main Signup Form Logic (Vercel API)
  const mainSignupForm = document.getElementById('main-signup-form');
  const signupMsgContainer = document.getElementById('signup-message-container');
  const signupSuccessView = document.getElementById('signup-success-view');

  if (mainSignupForm) {
    // Initialize Phone Country Picker
    const phoneInput = document.getElementById('signup-phone');
    let iti;
    if (phoneInput && typeof window.intlTelInput !== 'undefined') {
      iti = window.intlTelInput(phoneInput, {
        initialCountry: "us",
        separateDialCode: true,
        utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@23.0.4/build/js/utils.js",
      });
    }

    mainSignupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const formData = new FormData(mainSignupForm);
      
      // Get full phone number with country code if iti is initialized
      const phoneVal = iti ? iti.getNumber() : formData.get('phone');
      
      const data = {
        name: formData.get('name'),
        email: formData.get('email'),
        phone: phoneVal,
        message: `${formData.get('message')}${formData.get('message_extra') ? ' | Notes: ' + formData.get('message_extra') : ''}`
      };

      const submitBtn = mainSignupForm.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;

      // UI Loading State
      submitBtn.innerHTML = 'Sending Request... <i data-lucide="loader" class="spin"></i>';
      submitBtn.disabled = true;
      if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    
      
      signupMsgContainer.style.display = 'none';

      try {
        // Prepare data for Google Sheets
        const sheetData = new URLSearchParams();
        sheetData.append('name', formData.get('name'));
        sheetData.append('email', formData.get('email'));
        sheetData.append('phone', phoneVal);
        sheetData.append('message', `${formData.get('message')}${formData.get('message_extra') ? ' | Notes: ' + formData.get('message_extra') : ''}`);

        // 1. Submit to Google Sheets (Signup/New Sheet)
        await fetch(SIGNUP_WEBHOOK, {
          method: 'POST',
          mode: 'no-cors',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: sheetData
        });

        // 2. Submit to Vercel API (Backup & Emails)
        try {
          await fetch('/api/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
        } catch (vErr) {
          console.warn('Backup Vercel API failed:', vErr);
        }

        // Success - Data has been sent
        mainSignupForm.style.display = 'none';
        signupSuccessView.style.display = 'block';
        if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    
      } catch (error) {
        console.error('Signup Error:', error);
        // But if Sheets is the priority, we might treat it as success.
        // Given the request, we'll keep the error display.
        
        signupMsgContainer.style.display = 'block';
        signupMsgContainer.style.background = 'rgba(179, 65, 88, 0.1)';
        signupMsgContainer.style.color = 'var(--crimson)';
        signupMsgContainer.style.border = '1px solid rgba(179, 65, 88, 0.2)';
        signupMsgContainer.innerText = error.message || 'Unable to send request. Please try again later.';
        
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        if (typeof lucide !== 'undefined') lucide.createIcons();

            // Mobile Dropdown Toggle
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
    
      }
    });
  }

});
