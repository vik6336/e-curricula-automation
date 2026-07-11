# CurriculAI

CurriculAI takes the yearly e-curricula grind off faculty at SRM. You upload the SLO/SRO document for a course, Gemini generates all the session presentations, learning material and a full question bank, you review and edit whatever you want, and then the app fills the eCurricula portal for you through an automated browser.

It was built around the Containers and Cloud DevOps course (21CSE597T), but most of the pipeline is driven by the SLO document and a config file rather than anything course specific.

## The problem

A course coordinator has to upload a lot of content every year. For a typical 5 unit course:

- 18 PPTs per unit, one for each session/SLO pair, zipped and uploaded slot by slot
- a learning material PDF per unit
- at least 5 MCQs, 2 short answer and 1 long answer question per session, each entered in a web form with Bloom's level, a taxonomy verb and program outcome checkboxes

That works out to 90 slide decks and over 350 question form submissions, done manually in a portal that only accepts them one at a time. Most of a week goes into clicking.

## How it works

1. The professor opens the local web app and uploads the SLO/SRO document
2. Gemini generates a 9 slide deck per SLO (definition, motivation, procedure, diagram, code example, case study, quiz, summary), plus a references style learning material PDF per unit
3. The question generator produces the required MCQs, short and long questions per session, already tagged with Bloom's level, taxonomy verb and PO mapping
4. Everything can be downloaded and reviewed first. Questions have their own review PDF and an in-browser editor where you can rewrite anything or ask the AI to regenerate a single question with feedback
5. On publish, a real Chrome window opens on the eCurricula login page. The professor signs in and solves the captcha themselves, and the automation takes over from there: uploading every zip and PDF to the right slot and typing every question into the portal forms

The app never sees or stores portal credentials. Login happens entirely in the browser window, by the professor.

If the portal already has content in a slot (uploaded manually at some point), the automation stops and asks whether to replace it or keep it. Nothing gets overwritten silently.

## Running it

You need Python 3.11+, Node 18+ and a Gemini API key.

```bash
cp config/.env.example config/.env
# put your GEMINI_API_KEY in config/.env
./run.sh
```

`run.sh` installs dependencies, builds the UI and starts the server. Open http://localhost:8000.

To check your Gemini key works before a long run:

```bash
python3 test_gemini_key.py
```

This has to run locally on the professor's machine, not on a server. The portal login has a captcha, so the upload step needs a browser window the professor can actually see and type into.

## Stack

- FastAPI backend, single process, also serves the built UI
- React + Tailwind + framer-motion frontend
- Gemini for content generation, python-pptx and reportlab for file building
- Playwright driving Chrome for the portal upload

## Things to know

- The free Gemini tier gets rate limited hard on full course runs. Generation checkpoints after every SLO and every session, so an interrupted run resumes where it stopped instead of starting over. A paid tier removes the waiting.
- The portal enforces upload limits (zips under 1 MB, PDFs under 5 MB) and minimum question counts per session. The generator and the UI both respect these.
- The course code currently lives in `config/settings.yaml` and in `scripts/upload/portal_upload.py`. Pointing this at another course means updating those two places and supplying that course's SLO document.
- Generated content is a draft, not a final product. The review step exists because the model does occasionally mark a wrong MCQ answer or write a weak question, and a human should catch that before students see it.

## Layout

```
server.py                  FastAPI app and job orchestration
run.sh                     one command setup and start
scripts/
  ingest/                  SLO document and PDF parsing
  generate/                Gemini content and question generation
  build/                   PPT and PDF builders
  upload/                  Playwright portal automation
ui/                        React frontend
config/                    settings.yaml and .env
input/                     SLO document and syllabus
output/                    generated files, gitignored
```
