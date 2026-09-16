# ATS Resume Matcher

A small Flask web app that scores how well a resume matches a job description,
the way an Applicant Tracking System might: upload a resume (PDF or DOCX),
paste a job description, and get a match score with matched/missing keywords.

## How scoring works

- **Content similarity** — TF-IDF cosine similarity between the resume text
  and job description text.
- **Keyword coverage** — the most frequent, meaningful terms (unigrams and
  bigrams) are extracted from the job description, then checked for presence
  in the resume.
- **Overall score** — an even weighting of the two above.

This is a heuristic, not a guarantee of how any specific real-world ATS
scores a resume — different systems weight things differently.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

On macOS, port 5000 is often taken by the AirPlay Receiver. If you see
"Address already in use", either disable AirPlay Receiver in
System Settings → General → AirDrop & Handoff, or run on a different port:

```bash
PORT=5001 python app.py
```

## Notes

- Supported file types: `.pdf`, `.docx` (max 5 MB).
- Scanned/image-only PDFs won't extract text — use a text-based resume.

## Troubleshooting

**`ModuleNotFoundError` after `pip install`** — if `pip install -r requirements.txt`
printed a build error partway through, one of the packages likely failed to
install and the rest never ran. Always use a clean virtual environment
(as in Setup above) rather than installing into a conda `base` environment
or a system Python, which are more likely to have conflicting packages.
Then re-run `pip install -r requirements.txt` and check the full output for
which package failed.
