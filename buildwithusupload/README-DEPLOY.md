# Build With Us — deploy to tomoclub.org

What's in this package
  build-with-us/index.html        the page  ->  tomoclub.org/build-with-us/
  build-with-us/thank-you.html    shown after the form is submitted
  assets/press/xprize.jpg         the XPRIZE photo (only new image needed)

Everything else the page uses (team photos, partner logos, STEM.org badges,
styles) is already on tomoclub.org. The form posts to the Google Apps Script
endpoint that writes to "TomoClub – Build With Us leads (v2)".

Step by step (GitHub repo -> Vercel)
  1. Unzip build-with-us-upload.zip on your computer.
  2. Open the tomoclub.org website repo on GitHub.
  3. Add file -> Upload files. Drag the whole "build-with-us" folder in.
  4. Open the repo's "assets" folder. Add file -> Upload files. Drag the
     "press" folder (containing xprize.jpg) in.
  5. Commit changes to the main branch.
  6. Wait 1-2 minutes for Vercel to deploy, then open
     https://www.tomoclub.org/build-with-us/ and submit a test entry.
     A row should appear in the leads sheet and you should get the alert email.
  7. Add a link to /build-with-us/ in the homepage nav ("Build With Us").

If the site is deployed with the Vercel CLI instead of GitHub
  Unzip into the local website folder (next to index.html and styles.css),
  then run:  npx vercel --prod
