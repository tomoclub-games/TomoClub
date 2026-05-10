import os

file_path = 'script.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where to insert (after mainSignupForm logic)
insertion_point = -1
for i, line in enumerate(lines):
    if "mainSignupForm.addEventListener('submit'" in line:
        # Find the closing of this block
        brace_count = 0
        for j in range(i, len(lines)):
            brace_count += lines[j].count('{')
            brace_count -= lines[j].count('}')
            if brace_count == 0 and j > i:
                insertion_point = j + 2 # After the closing } and if(mainSignupForm){ }
                break
        if insertion_point != -1:
            break

new_logic = """
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
"""

if insertion_point != -1:
    lines.insert(insertion_point, new_logic)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Successfully updated script.js")
else:
    print("Could not find insertion point")
