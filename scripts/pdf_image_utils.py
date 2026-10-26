"""
Shared helper for pulling embedded images out of a source PDF, used by
both add_article.py and add_blog_post.py when a user supplies a PDF as
the source document for a new post/article.

Deciding WHICH extracted images are actually worth embedding, where they
go in the content, and what alt text/caption to give them is a judgment
call for whoever is writing the content (human or agent) -- this module
only does the mechanical extraction.
"""

import os


def extract_pdf_images(pdf_path: str, out_dir: str):
    """Extract every embedded image from pdf_path into out_dir, named
    page<N>-img<i>.<ext>. Returns a list of dicts: {page, path, width,
    height}, ordered by page then position, so the caller can review them
    (e.g. with the Read tool) and pick the ones worth keeping.

    Requires PyMuPDF ("pip install pymupdf"); raises ImportError with
    that instruction if it's missing.

    Note: this extracts images embedded as XObjects in the PDF. It will
    NOT produce anything for a PDF where the "images" are actually just
    text/vector content that merely looks like a graphic -- in that case
    there's nothing to extract.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDF is required for PDF image extraction. Install it with: pip install pymupdf"
        )

    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    results = []
    for pno in range(len(doc)):
        page = doc[pno]
        for i, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base = doc.extract_image(xref)
            ext = base['ext']
            out_path = os.path.join(out_dir, f"page{pno + 1}-img{i + 1}.{ext}")
            with open(out_path, 'wb') as f:
                f.write(base['image'])
            results.append({
                'page': pno + 1,
                'path': out_path,
                'width': base.get('width'),
                'height': base.get('height'),
            })
    return results


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf_path')
    parser.add_argument('out_dir')
    args = parser.parse_args()

    try:
        results = extract_pdf_images(args.pdf_path, args.out_dir)
    except ImportError as e:
        print(e)
        sys.exit(1)

    if not results:
        print("No embedded images found in this PDF.")
    for r in results:
        print(f"page {r['page']}: {r['path']} ({r['width']}x{r['height']})")
