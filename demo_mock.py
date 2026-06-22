"""Demo script — generates PPT + PDF files using mock data (no API key needed).

Uses the new 9-slide schema: title, what, why, how, diagram, code, use_case, quiz, summary.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scripts.build.create_ppt import create_module_ppts
from scripts.build.create_pdf import create_module_pdf


# ---------------------------------------------------------------------------
# Mock SLO content — one full 9-slide deck per SLO (new schema)
# ---------------------------------------------------------------------------

MOCK_SLOS = [
    # Session 1 SLO 1
    {
        "session_num": 1, "slo_num": 1,
        "slo_text": "Explain the Docker ecosystem and container fundamentals",
        "content": {
            "slo_title": "Docker Ecosystem & Container Fundamentals",
            "course_code": "21CSE597T",
            "module_num": 1,
            "session_num": 1,
            "slo_num": 1,
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "title",
                    "layout": "title_slide",
                    "title": "Docker Ecosystem & Container Fundamentals",
                    "subtitle": "Explain the Docker ecosystem and container fundamentals",
                    "hook": "Shipping code used to take weeks — containers make it take seconds.",
                    "speaker_notes": "Open with a question: how many of you have heard 'it works on my machine'? That's exactly the problem Docker was built to solve."
                },
                {
                    "slide_number": 2,
                    "slide_type": "what",
                    "layout": "two_col",
                    "title": "What is Docker?",
                    "definition": "Docker is an open-source platform that automates the deployment of applications inside lightweight, portable containers. A container packages the application code, runtime, libraries, and configuration into a single self-contained unit that runs identically across any environment.",
                    "key_characteristics": [
                        "Lightweight — shares host OS kernel, no full VM overhead",
                        "Portable — runs on any machine with Docker installed",
                        "Immutable — container images are read-only snapshots",
                        "Fast — containers start in milliseconds, not minutes"
                    ],
                    "analogy": "A Docker container is like a shipping container — standardised, stackable, and works on any ship (machine) without modification.",
                    "speaker_notes": "Emphasise the difference between VMs and containers. VMs virtualise hardware; containers virtualise the OS. This makes containers 10–100x lighter."
                },
                {
                    "slide_number": 3,
                    "slide_type": "why",
                    "layout": "content",
                    "title": "Why Docker Matters",
                    "problem_statement": "Developers waste 20–30% of their time on environment inconsistencies — code that works locally but fails in staging or production.",
                    "bullet_points": [
                        "Eliminates 'works on my machine' by packaging dependencies alongside the application",
                        "Reduces deployment time from hours to minutes with pre-built images",
                        "Enables microservices architecture — each service runs in an isolated container",
                        "Cuts infrastructure costs by packing more workloads onto the same host"
                    ],
                    "industry_context": "Netflix uses Docker to deploy 100+ times per day across 1,000+ microservices, achieving 99.99% uptime.",
                    "speaker_notes": "Connect this to the SRM campus context — in a team project, Docker means everyone runs the exact same environment regardless of whether they use Windows, Mac, or Linux."
                },
                {
                    "slide_number": 4,
                    "slide_type": "how",
                    "layout": "two_col",
                    "title": "How Docker Works",
                    "steps": [
                        "Write a Dockerfile defining the base image, dependencies, and startup command",
                        "Run docker build to create an immutable image layer by layer",
                        "Push the image to a registry (Docker Hub, AWS ECR, GitHub Container Registry)",
                        "Run docker run to start a container from the image on any host",
                        "Use Docker Compose to orchestrate multi-container applications locally"
                    ],
                    "tools": [
                        {"name": "Docker Engine",   "role": "Core runtime that builds and runs containers"},
                        {"name": "Docker Hub",      "role": "Public registry for storing and sharing images"},
                        {"name": "Docker Compose",  "role": "YAML-based tool to run multi-container apps"},
                        {"name": "Docker Desktop",  "role": "GUI + CLI for local development on Mac/Windows"}
                    ],
                    "speaker_notes": "Walk through each step on the board. Step 3 is often skipped in local dev but essential for CI/CD. Ask students which tools they've already used."
                },
                {
                    "slide_number": 5,
                    "slide_type": "diagram",
                    "layout": "diagram",
                    "title": "Docker Architecture",
                    "diagram": {
                        "nodes": [
                            {"id": "client",    "label": "Docker Client",   "shape": "box",     "color": "#C8102E", "font_color": "#FFFFFF"},
                            {"id": "daemon",    "label": "Docker Daemon",   "shape": "box",     "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "images",    "label": "Images",          "shape": "rounded", "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "containers","label": "Containers",      "shape": "rounded", "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "registry",  "label": "Docker Registry", "shape": "box",     "color": "#2E7D32", "font_color": "#FFFFFF"}
                        ],
                        "edges": [
                            {"from": "client",    "to": "daemon",     "label": "REST API",  "arrow": True},
                            {"from": "daemon",    "to": "images",     "label": "manages",   "arrow": True},
                            {"from": "daemon",    "to": "containers", "label": "runs",      "arrow": True},
                            {"from": "daemon",    "to": "registry",   "label": "push/pull", "arrow": True}
                        ],
                        "layout_direction": "left_to_right",
                        "caption": "Docker client sends commands via REST API to the daemon, which manages images, containers, and communicates with registries."
                    },
                    "speaker_notes": "Point out that the client and daemon can run on different machines — this is how remote Docker hosts work and how CI servers pull images."
                },
                {
                    "slide_number": 6,
                    "slide_type": "code",
                    "layout": "code_block",
                    "title": "Your First Dockerfile",
                    "code_snippet": "# Use official Python 3.11 slim image as base\nFROM python:3.11-slim\n\n# Set working directory inside container\nWORKDIR /app\n\n# Copy requirements first (layer caching optimisation)\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Copy application source code\nCOPY . .\n\n# Expose port and define startup command\nEXPOSE 8080\nCMD [\"python\", \"app.py\"]",
                    "language": "dockerfile",
                    "explanation": [
                        {"line_ref": "Line 2",   "note": "slim variant reduces image size by ~60% vs full Python image"},
                        {"line_ref": "Lines 8–9", "note": "copying requirements before source code exploits Docker layer cache — only reinstalls packages when requirements.txt changes"},
                        {"line_ref": "Line 15",  "note": "CMD sets default command; can be overridden at runtime with docker run ... python shell.py"}
                    ],
                    "speaker_notes": "Run this live if possible. Show docker build -t myapp . then docker run -p 8080:8080 myapp. The layer caching point is key for fast CI builds."
                },
                {
                    "slide_number": 7,
                    "slide_type": "use_case",
                    "layout": "two_col",
                    "title": "Real-World Use Case",
                    "company": "Spotify",
                    "scenario": "Spotify managed 1,800+ microservices across multiple data centres. Each team had different language runtimes and dependency versions, causing deployment conflicts and 4-hour average release cycles.",
                    "solution": "Migrated all services to Docker containers with standardised Dockerfile templates. Built a shared internal registry and Helm charts for Kubernetes deployment.",
                    "outcome": "Deployment time dropped from 4 hours to 12 minutes. Environment-related bugs fell by 75%. 200+ deployments per day with zero-downtime rolling updates.",
                    "lesson": "Standardising on Docker images as the deployment unit — not code — is the single highest-leverage change a team can make.",
                    "speaker_notes": "Ask students: if each of your project team members uses a different Python version, how does Docker solve that? Let them articulate the answer."
                },
                {
                    "slide_number": 8,
                    "slide_type": "quiz",
                    "layout": "quiz",
                    "title": "Knowledge Check",
                    "question": "A developer builds a Docker image on Windows and pushes it to Docker Hub. A colleague pulls and runs it on Linux. What will happen?",
                    "options": {
                        "A": "It will fail — Docker images are OS-specific",
                        "B": "It will run identically, because the container includes all dependencies",
                        "C": "It will run but slower, due to OS translation overhead",
                        "D": "It will fail unless both machines have the same Docker version"
                    },
                    "correct_answer": "B",
                    "explanation": "Docker images are portable across any host with Docker installed because they bundle all application dependencies. The container shares the host kernel but is otherwise self-contained. OS version and host language are irrelevant.",
                    "challenge_task": "Write a Dockerfile for a simple Flask app, build it locally, run it on port 5000, and verify it works with curl http://localhost:5000",
                    "speaker_notes": "Give 60 seconds of think time. Most students guess A. Use the correct answer to reinforce the core value proposition of containers."
                },
                {
                    "slide_number": 9,
                    "slide_type": "summary",
                    "layout": "summary",
                    "title": "Key Takeaways",
                    "bullet_points": [
                        "WHAT: Docker packages apps + dependencies into portable, immutable containers",
                        "WHY: Eliminates environment drift, cuts deploy time, enables microservices at scale",
                        "HOW: Dockerfile → docker build → registry push → docker run on any host",
                        "USE CASE: Spotify cut release time from 4 hrs to 12 min with container standardisation"
                    ],
                    "call_to_action": "Install Docker Desktop and run docker run hello-world to verify your setup",
                    "preview": "Next — Docker CLI deep dive: managing images, volumes, networks, and multi-stage builds",
                    "speaker_notes": "Recap by asking a student to explain in one sentence what Docker does and why it matters. Assign the challenge task as homework if not completed in class."
                }
            ]
        }
    },

    # Session 1 SLO 2
    {
        "session_num": 1, "slo_num": 2,
        "slo_text": "Demonstrate Docker CLI commands for image and container management",
        "content": {
            "slo_title": "Docker CLI & Container Management",
            "course_code": "21CSE597T",
            "module_num": 1,
            "session_num": 1,
            "slo_num": 2,
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "title",
                    "layout": "title_slide",
                    "title": "Docker CLI & Container Management",
                    "subtitle": "Demonstrate Docker CLI commands for image and container management",
                    "hook": "Mastering 10 Docker commands puts you ahead of 80% of developers in cloud job interviews.",
                    "speaker_notes": "This session is hands-on — students should have Docker Desktop open. Every command we cover should be typed, not just watched."
                },
                {
                    "slide_number": 2,
                    "slide_type": "what",
                    "layout": "two_col",
                    "title": "What is the Docker CLI?",
                    "definition": "The Docker CLI (Command Line Interface) is the primary tool for interacting with the Docker daemon. It provides commands to build, run, inspect, stop, and remove containers and images. Every Docker workflow — from local development to CI/CD pipelines — relies on CLI commands.",
                    "key_characteristics": [
                        "Communicates with Docker daemon via REST API",
                        "Context-aware — can switch between local and remote daemons",
                        "Scriptable — all commands return exit codes for automation",
                        "Composable — combine with shell pipes and scripts"
                    ],
                    "analogy": "The Docker CLI is like a TV remote — you don't need to understand the electronics inside; you just press the right buttons to get the right result.",
                    "speaker_notes": "Emphasise that the CLI is not just for devs — ops, SREs, and platform engineers use it daily in production for debugging and incident response."
                },
                {
                    "slide_number": 3,
                    "slide_type": "why",
                    "layout": "content",
                    "title": "Why CLI Mastery is Critical",
                    "problem_statement": "GUI tools abstract away control — in production incidents, you have only a terminal and seconds to diagnose a failing container.",
                    "bullet_points": [
                        "All CI/CD pipelines execute Docker commands via CLI — GUIs don't run in automated pipelines",
                        "Remote servers have no desktop — SSH + CLI is the only interface in production",
                        "Scripted docker commands enable repeatable, auditable operations across environments",
                        "Docker Compose and Kubernetes kubectl follow the same CLI patterns — learning one transfers"
                    ],
                    "industry_context": "AWS, GCP, and Azure cloud certifications test Docker CLI knowledge directly in hands-on lab assessments.",
                    "speaker_notes": "Ask: how many of you plan to work in cloud or DevOps? Every one of those jobs involves CLI daily. This is not optional knowledge."
                },
                {
                    "slide_number": 4,
                    "slide_type": "how",
                    "layout": "two_col",
                    "title": "Essential CLI Workflow",
                    "steps": [
                        "docker pull <image> — download an image from a registry to local cache",
                        "docker build -t <name>:<tag> . — build an image from local Dockerfile",
                        "docker run -d -p 8080:80 <image> — start a detached container with port mapping",
                        "docker ps / docker ps -a — list running / all containers with their status",
                        "docker logs <container> / docker exec -it <container> sh — inspect and debug"
                    ],
                    "tools": [
                        {"name": "docker images",  "role": "List locally cached images with sizes and tags"},
                        {"name": "docker inspect", "role": "Output full JSON metadata for any container or image"},
                        {"name": "docker stats",   "role": "Live CPU, memory, and network usage per container"},
                        {"name": "docker system",  "role": "Disk usage overview and cleanup (prune)"}
                    ],
                    "speaker_notes": "Type each command live. Show docker stats in one terminal while running a container in another — the live feed impresses students and shows real utility."
                },
                {
                    "slide_number": 5,
                    "slide_type": "diagram",
                    "layout": "diagram",
                    "title": "Container Lifecycle",
                    "diagram": {
                        "nodes": [
                            {"id": "created",  "label": "Created",   "shape": "rounded", "color": "#666666", "font_color": "#FFFFFF"},
                            {"id": "running",  "label": "Running",   "shape": "rounded", "color": "#2E7D32", "font_color": "#FFFFFF"},
                            {"id": "paused",   "label": "Paused",    "shape": "rounded", "color": "#F57C00", "font_color": "#FFFFFF"},
                            {"id": "stopped",  "label": "Stopped",   "shape": "rounded", "color": "#C8102E", "font_color": "#FFFFFF"},
                            {"id": "removed",  "label": "Removed",   "shape": "rounded", "color": "#1B365D", "font_color": "#FFFFFF"}
                        ],
                        "edges": [
                            {"from": "created", "to": "running", "label": "docker start",  "arrow": True},
                            {"from": "running", "to": "paused",  "label": "docker pause",  "arrow": True},
                            {"from": "paused",  "to": "running", "label": "docker unpause","arrow": True},
                            {"from": "running", "to": "stopped", "label": "docker stop",   "arrow": True},
                            {"from": "stopped", "to": "removed", "label": "docker rm",     "arrow": True}
                        ],
                        "layout_direction": "left_to_right",
                        "caption": "A container transitions through Created → Running → Stopped → Removed. Paused is a suspended Running state."
                    },
                    "speaker_notes": "Walk through the lifecycle as you demonstrate each command in the terminal. Show docker ps -a to show stopped containers that haven't been removed yet."
                },
                {
                    "slide_number": 6,
                    "slide_type": "code",
                    "layout": "code_block",
                    "title": "Debug a Running Container",
                    "code_snippet": "# List running containers\ndocker ps\n\n# Tail the last 50 log lines and follow new output\ndocker logs --tail 50 -f my-app\n\n# Open an interactive shell inside the container\ndocker exec -it my-app /bin/sh\n\n# Inspect full container config as JSON\ndocker inspect my-app | grep -A5 '\"IPAddress\"'\n\n# Check live resource usage\ndocker stats my-app --no-stream",
                    "language": "bash",
                    "explanation": [
                        {"line_ref": "Line 5",    "note": "-f flag streams new log lines in real time, like tail -f — essential during deploys"},
                        {"line_ref": "Line 8",    "note": "exec -it opens an interactive TTY shell inside the running container without stopping it"},
                        {"line_ref": "Lines 11–14","note": "inspect returns ~100 lines of JSON; pipe to grep to extract the field you need quickly"}
                    ],
                    "speaker_notes": "Run this against a running nginx container. Show that exec -it lets you browse the container filesystem live — great for debugging missing files or permissions."
                },
                {
                    "slide_number": 7,
                    "slide_type": "use_case",
                    "layout": "two_col",
                    "title": "Real-World Use Case",
                    "company": "Airbnb Engineering",
                    "scenario": "Airbnb's on-call engineers were spending 45 minutes per incident tracing crashes in production containers. Log aggregation was delayed and SSH access to hosts was restricted by security policies.",
                    "solution": "Standardised on docker logs + docker exec workflows with a wrapper script that auto-fetched the 3 most recent error log lines and container resource stats on every PagerDuty alert.",
                    "outcome": "Mean time to diagnosis dropped from 45 minutes to 6 minutes. On-call toil reduced by 40%. Junior engineers could handle Tier 2 incidents without escalation.",
                    "lesson": "Automating the first 3 debug commands you always run reduces cognitive load during high-stress incidents.",
                    "speaker_notes": "Ask students to think about their final-year projects: when your Flask app crashes at 2am before a demo, which Docker command do you run first?"
                },
                {
                    "slide_number": 8,
                    "slide_type": "quiz",
                    "layout": "quiz",
                    "title": "Knowledge Check",
                    "question": "You run docker stop my-app. A colleague runs docker ps and reports the container is not listed. Where has it gone and how do you retrieve it?",
                    "options": {
                        "A": "It is permanently deleted — you must rebuild the image",
                        "B": "It is in Stopped state — visible with docker ps -a and restartable with docker start my-app",
                        "C": "It moved to a paused state — use docker unpause my-app",
                        "D": "It is cached in the registry — use docker pull to restore it"
                    },
                    "correct_answer": "B",
                    "explanation": "docker stop sends SIGTERM to the container, transitioning it to Stopped state. Stopped containers still exist on disk and are visible with docker ps -a. They can be restarted with docker start or permanently deleted with docker rm.",
                    "challenge_task": "Run an nginx container detached on port 8080, view its logs, open a shell inside it, then cleanly stop and remove it — all using CLI commands only.",
                    "speaker_notes": "This question reveals a very common misconception. Let students discuss for 60s. Reinforce: docker stop ≠ docker rm. Use docker system prune to show what's still on disk."
                },
                {
                    "slide_number": 9,
                    "slide_type": "summary",
                    "layout": "summary",
                    "title": "Key Takeaways",
                    "bullet_points": [
                        "WHAT: Docker CLI is the control interface for every container lifecycle operation",
                        "WHY: All production, CI/CD, and cloud environments are terminal-only — GUI is not enough",
                        "HOW: pull → build → run → ps → logs/exec is the core debug loop",
                        "USE CASE: Airbnb cut incident response time by 7x with standardised CLI debug scripts"
                    ],
                    "call_to_action": "Complete the challenge task and push your Dockerfile to a GitHub repo",
                    "preview": "Next session — DevOps toolchain and building your first CI/CD pipeline with GitHub Actions",
                    "speaker_notes": "Cold-call a student to explain docker ps vs docker ps -a. Assign challenge task. Remind students that the upcoming lab assessment covers these exact commands."
                }
            ]
        }
    },

    # Session 2 SLO 1
    {
        "session_num": 2, "slo_num": 1,
        "slo_text": "Describe the DevOps toolchain and CI/CD pipeline concepts",
        "content": {
            "slo_title": "DevOps Toolchain & CI/CD Pipelines",
            "course_code": "21CSE597T",
            "module_num": 1,
            "session_num": 2,
            "slo_num": 1,
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "title",
                    "layout": "title_slide",
                    "title": "DevOps Toolchain & CI/CD Pipelines",
                    "subtitle": "Describe the DevOps toolchain and CI/CD pipeline concepts",
                    "hook": "Every 11.7 seconds, a new commit is deployed to Amazon production — CI/CD is why.",
                    "speaker_notes": "Open with a comparison: how long does it take your team to push a change from code to users? The answer for most companies used to be weeks. CI/CD makes it minutes."
                },
                {
                    "slide_number": 2,
                    "slide_type": "what",
                    "layout": "two_col",
                    "title": "What is a CI/CD Pipeline?",
                    "definition": "A CI/CD pipeline is an automated software delivery process that continuously integrates code changes (CI) and automatically deploys validated builds to target environments (CD). It replaces manual, error-prone release processes with a repeatable, auditable workflow triggered by every code commit.",
                    "key_characteristics": [
                        "Triggered automatically on every git push or pull request",
                        "Stages run sequentially — a failing stage blocks downstream deployment",
                        "Artifacts (Docker images, binaries) are immutable and version-tagged",
                        "Full audit trail — who triggered what, when, and with what result"
                    ],
                    "analogy": "A CI/CD pipeline is like a factory assembly line — raw material (code) enters one end, and a tested, packaged product (deployable build) comes out the other, automatically.",
                    "speaker_notes": "Distinguish CI from CD: CI is the build+test automation; CD is the deployment automation. Some teams do CI without CD (manual deployment gate). Both have value independently."
                },
                {
                    "slide_number": 3,
                    "slide_type": "why",
                    "layout": "content",
                    "title": "Why CI/CD is Non-Negotiable",
                    "problem_statement": "Manual release processes take 2–8 weeks and introduce human error — merge conflicts discovered late, untested code reaching production, no rollback path.",
                    "bullet_points": [
                        "Detects integration bugs within minutes of commit, not days before release",
                        "Reduces deployment risk by releasing smaller, more frequent changes",
                        "Enables feature flags and canary deployments for controlled rollouts",
                        "Frees engineers from manual release work — hours of toil eliminated per sprint"
                    ],
                    "industry_context": "Google deploys to production over 5,500 times per day — impossible without fully automated CI/CD across 2 billion lines of code.",
                    "speaker_notes": "The key insight: more frequent deployments are LESS risky, not more, because each change is smaller and easier to diagnose. This counter-intuitive point is worth dwelling on."
                },
                {
                    "slide_number": 4,
                    "slide_type": "how",
                    "layout": "two_col",
                    "title": "How a CI/CD Pipeline Works",
                    "steps": [
                        "Developer pushes code to Git — pipeline is triggered automatically via webhook",
                        "CI stage: code is compiled/linted, unit tests run, coverage threshold enforced",
                        "Build stage: Docker image is built, tagged with commit SHA, pushed to registry",
                        "Staging deploy: image is deployed to staging environment, integration tests run",
                        "Production deploy: approved build promoted to production via blue/green or canary"
                    ],
                    "tools": [
                        {"name": "GitHub Actions", "role": "YAML-based CI/CD workflows triggered by git events"},
                        {"name": "Jenkins",         "role": "Self-hosted pipeline orchestration with plugin ecosystem"},
                        {"name": "ArgoCD",          "role": "GitOps-based continuous deployment for Kubernetes"},
                        {"name": "SonarQube",       "role": "Static code analysis and quality gate enforcement"}
                    ],
                    "speaker_notes": "Draw the pipeline stages on the board as you explain each one. Emphasise that each stage produces an artifact that the next stage consumes — this is what makes pipelines composable."
                },
                {
                    "slide_number": 5,
                    "slide_type": "diagram",
                    "layout": "diagram",
                    "title": "CI/CD Pipeline Flow",
                    "diagram": {
                        "nodes": [
                            {"id": "code",    "label": "Code Commit",     "shape": "box",     "color": "#C8102E", "font_color": "#FFFFFF"},
                            {"id": "ci",      "label": "CI: Test + Lint", "shape": "box",     "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "build",   "label": "Build Image",     "shape": "box",     "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "staging", "label": "Deploy Staging",  "shape": "box",     "color": "#1B365D", "font_color": "#FFFFFF"},
                            {"id": "prod",    "label": "Deploy Prod",     "shape": "box",     "color": "#2E7D32", "font_color": "#FFFFFF"}
                        ],
                        "edges": [
                            {"from": "code",    "to": "ci",      "label": "webhook",   "arrow": True},
                            {"from": "ci",      "to": "build",   "label": "tests pass","arrow": True},
                            {"from": "build",   "to": "staging", "label": "push image","arrow": True},
                            {"from": "staging", "to": "prod",    "label": "approved",  "arrow": True}
                        ],
                        "layout_direction": "left_to_right",
                        "caption": "Each stage gates the next — a failing test blocks the image build, preventing broken code from ever reaching production."
                    },
                    "speaker_notes": "Point out the fail-fast principle: detecting failures at the earliest (cheapest) stage. A unit test failure at Stage 2 saves the cost of a production incident at Stage 5."
                },
                {
                    "slide_number": 6,
                    "slide_type": "code",
                    "layout": "code_block",
                    "title": "GitHub Actions CI/CD Workflow",
                    "code_snippet": "name: CI/CD Pipeline\non:\n  push:\n    branches: [main]\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: pip install -r requirements.txt\n      - run: pytest --cov=app tests/\n\n  build-push:\n    needs: test\n    runs-on: ubuntu-latest\n    steps:\n      - uses: docker/build-push-action@v4\n        with:\n          push: true\n          tags: myapp:${{ github.sha }}",
                    "language": "yaml",
                    "explanation": [
                        {"line_ref": "Lines 2–4",  "note": "on.push.branches: [main] triggers the pipeline only on commits to main — feature branches don't trigger deployment"},
                        {"line_ref": "Line 13",    "note": "needs: test creates an explicit dependency — build-push only runs if the test job succeeds"},
                        {"line_ref": "Line 19",    "note": "tagging with github.sha (commit hash) makes every image uniquely traceable to its source code"}
                    ],
                    "speaker_notes": "Show this file in a real GitHub repo. Navigate to the Actions tab to show the visual pipeline graph. The needs: keyword is the core of pipeline dependency management."
                },
                {
                    "slide_number": 7,
                    "slide_type": "use_case",
                    "layout": "two_col",
                    "title": "Real-World Use Case",
                    "company": "Etsy",
                    "scenario": "Etsy was releasing code twice a week with a team of 40 engineers coordinating manual deployments. Each release required a 4-hour deployment window, a war room of engineers, and a rollback plan that was never tested.",
                    "solution": "Adopted Continuous Deployment with automated testing gates, feature flags, and a self-service deployment tool (Deployinator). Any engineer could deploy any time.",
                    "outcome": "Deployments increased from 2/week to 50+/day. Deployment-related incidents fell by 90%. Engineer productivity rose 25% as release coordination overhead was eliminated.",
                    "lesson": "The biggest risk in deployment is the size of the change, not the frequency — CI/CD reduces risk by making every change small.",
                    "speaker_notes": "Etsy's story is well documented in 'Continuous Delivery' by Jez Humble. The war room → self-service shift is a cultural change as much as a technical one."
                },
                {
                    "slide_number": 8,
                    "slide_type": "quiz",
                    "layout": "quiz",
                    "title": "Knowledge Check",
                    "question": "In a CI/CD pipeline, the build stage fails because a Docker registry authentication token has expired. Which stage runs next?",
                    "options": {
                        "A": "The staging deploy stage runs with the last successful build",
                        "B": "The pipeline pauses and waits for manual intervention",
                        "C": "No further stages run — the pipeline fails at the build stage",
                        "D": "The production deploy stage is skipped but staging still runs"
                    },
                    "correct_answer": "C",
                    "explanation": "CI/CD pipelines are sequential with hard gates. If any stage fails, all downstream stages are blocked. This prevents partially-built or untested artifacts from reaching production. The needs: dependency in GitHub Actions enforces this behaviour explicitly.",
                    "challenge_task": "Create a GitHub Actions workflow that runs pytest on push to main, then builds a Docker image and prints its SHA tag — no actual push to a registry required.",
                    "speaker_notes": "Option A is the most common wrong answer — students assume pipelines are resilient. The correct answer enforces the core principle: fail fast, fail early, never deploy broken builds."
                },
                {
                    "slide_number": 9,
                    "slide_type": "summary",
                    "layout": "summary",
                    "title": "Key Takeaways",
                    "bullet_points": [
                        "WHAT: CI/CD automates the entire path from code commit to production deployment",
                        "WHY: Faster releases, fewer bugs, zero manual toil — essential for any modern engineering team",
                        "HOW: Git webhook → test → build image → deploy staging → promote to prod",
                        "USE CASE: Etsy went from 2 deploys/week to 50+/day, cutting incidents by 90%"
                    ],
                    "call_to_action": "Set up a free GitHub Actions workflow on your project repository today",
                    "preview": "Next — implementing a full CI/CD pipeline with Git branching strategies and Docker multi-stage builds",
                    "speaker_notes": "End with a show of hands: who can now explain what CI/CD does to a non-technical manager in one sentence? Pick someone to try. That's the real test of understanding."
                }
            ]
        }
    },
]


# ---------------------------------------------------------------------------
# Assemble module content and run build
# ---------------------------------------------------------------------------

slo_contents = [
    {
        "module_num": 1,
        "session_num": item["session_num"],
        "slo_num":     item["slo_num"],
        "slo_text":    item["slo_text"],
        "content":     item["content"],
    }
    for item in MOCK_SLOS
]

mock_pdf_content = {
    "module_title": "Container Fundamentals & DevOps",
    "introduction": (
        "This module introduces the foundational concepts of containerisation and DevOps practices "
        "that form the backbone of modern software delivery. Students will explore the Docker ecosystem, "
        "understand container fundamentals, learn essential DevOps toolchain components, and master "
        "Git-based version control workflows. By the end of this module, students will be able to "
        "create, manage, and deploy containerised applications using industry-standard tools and practices."
    ),
    "sessions": [
        {
            "session_number": 1,
            "title": "Docker Ecosystem & Container Management",
            "slo_1_title": "Docker Ecosystem & Container Fundamentals",
            "slo_2_title": "Docker CLI & Container Management",
            "content": (
                "Containers have revolutionised how software is developed, shipped, and run in production. "
                "Docker packages an application with all its dependencies into a single portable unit that "
                "runs consistently across any environment. The Docker CLI provides the control interface for "
                "every container lifecycle operation — from building images to debugging running containers "
                "with docker exec and docker logs."
            )
        },
        {
            "session_number": 2,
            "title": "DevOps Toolchain & CI/CD Implementation",
            "slo_1_title": "DevOps Toolchain & CI/CD Pipelines",
            "slo_2_title": "Building CI/CD with Git & Docker",
            "content": (
                "The DevOps toolchain encompasses the tools and practices that enable continuous integration "
                "and delivery. A CI/CD pipeline automates the build, test, and deployment process, reducing "
                "manual intervention and accelerating delivery. GitHub Actions provides a YAML-based "
                "orchestration layer where each stage gates the next, ensuring broken code never reaches "
                "production. Etsy's transformation from 2 to 50+ deployments per day exemplifies the impact."
            )
        },
    ],
    "conclusion": (
        "This module has covered the essential building blocks of containerisation and DevOps. "
        "Docker fundamentals, CLI mastery, and CI/CD pipeline design form the foundation for the "
        "advanced topics in subsequent modules including Kubernetes, AWS services, and infrastructure as code."
    ),
}

module_content = {
    "module_num": 1,
    "module_title": "Container Fundamentals & DevOps",
    "slo_contents": slo_contents,
    "pdf_content": mock_pdf_content,
}

output_dir = str(Path(__file__).parent / "output" / "21CSE597T")

print("=" * 60)
print("DEMO: Building files from mock data (no API key needed)")
print("=" * 60)

print(f"\nGenerating {len(slo_contents)} PPTX files...")
ppt_files = create_module_ppts(module_content, output_dir)
print(f"\n✓ Created {len(ppt_files)} PPTX files")

print("\nGenerating PDF for Module 1...")
pdf_path = Path(output_dir) / "unit_1" / "unit_1_learning_material.pdf"
create_module_pdf(mock_pdf_content, 1, str(pdf_path))
print(f"✓ Created PDF: {pdf_path}")

content_json_path = Path(output_dir) / "unit_1" / "content.json"
content_json_path.parent.mkdir(parents=True, exist_ok=True)
with open(content_json_path, "w") as f:
    json.dump(module_content, f, indent=2)
print(f"✓ Saved content JSON: {content_json_path}")

print("\n" + "=" * 60)
print("OUTPUT FILES:")
print("=" * 60)
unit_dir = Path(output_dir) / "unit_1"
for fp in sorted(unit_dir.rglob("*")):
    if fp.is_file():
        size_kb = fp.stat().st_size / 1024
        print(f"  {fp.relative_to(Path(output_dir))}  ({size_kb:.1f} KB)")
