css_to_add = """
.btn-read-more {
  margin-top: auto;
  padding: 0.6rem 1.2rem !important;
  font-size: 0.9rem !important;
  align-self: flex-start;
}

.btn-view-more {
  display: inline-flex !important;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.5rem !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  text-decoration: none;
}
"""

with open('styles.css', 'a') as f:
    f.write(css_to_add)
