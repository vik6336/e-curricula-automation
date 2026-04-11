"""Demo script — generates PPT + PDF files using mock data (no API key needed).

This simulates what Gemini would return and feeds it into the Build stage,
so you can see the actual output files.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scripts.build.create_ppt import create_module_ppts
from scripts.build.create_pdf import create_module_pdf

# ─── Mock data: what Gemini would return for Module 1 ───

def make_slo_content(session_num, slo_num, slo_text, topic):
    """Create mock Gemini output for one SLO (8 slides)."""
    return {
        "slo_title": topic,
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "title",
                "title": topic,
                "subtitle": slo_text,
                "bullet_points": [],
                "speaker_notes": f"Welcome to Session {session_num}, SLO {slo_num}. Today we will cover {topic}."
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "title": f"Introduction to {topic}",
                "subtitle": "",
                "bullet_points": [
                    f"{topic} is a foundational concept in modern cloud-native infrastructure and DevOps practices.",
                    "Organizations worldwide are adopting these technologies to improve deployment speed and reliability.",
                    "Understanding this concept is critical for any DevOps engineer working in production environments.",
                    "We will explore both the theory and practical applications in this session."
                ],
                "speaker_notes": f"Let's start with the basics of {topic} and understand why it matters."
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "title": "Core Concepts",
                "subtitle": "",
                "bullet_points": [
                    "Isolation and encapsulation provide the foundation for repeatable, consistent deployments across environments.",
                    "Declarative configuration enables infrastructure as code, reducing manual intervention and human error.",
                    "Immutable infrastructure patterns ensure that deployments are predictable and rollbacks are straightforward.",
                    "Service discovery and networking allow microservices to communicate seamlessly within a cluster."
                ],
                "speaker_notes": "These core concepts form the backbone of modern container orchestration."
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "title": "Architecture Overview",
                "subtitle": "",
                "bullet_points": [
                    "The control plane manages cluster state, scheduling, and API operations for all workloads.",
                    "Worker nodes execute containerized applications and report status back to the control plane.",
                    "Networking plugins (CNI) provide pod-to-pod communication across the cluster.",
                    "Storage plugins (CSI) enable persistent data storage for stateful applications."
                ],
                "speaker_notes": "The architecture is designed for scalability and fault tolerance."
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "title": "Hands-On Example",
                "subtitle": "",
                "bullet_points": [
                    "Step 1: Create a Dockerfile that packages your application with all dependencies.",
                    "Step 2: Build and push the container image to a registry (e.g., AWS ECR, Docker Hub).",
                    "Step 3: Write a deployment manifest specifying replicas, resource limits, and health checks.",
                    "Step 4: Apply the configuration and verify the deployment is running correctly."
                ],
                "speaker_notes": "Let's walk through a practical example to solidify these concepts."
            },
            {
                "slide_number": 6,
                "slide_type": "content",
                "title": "Best Practices",
                "subtitle": "",
                "bullet_points": [
                    "Always use multi-stage builds to minimize image size and reduce the attack surface.",
                    "Implement health checks (liveness and readiness probes) for production-grade deployments.",
                    "Use resource requests and limits to prevent noisy-neighbour issues in shared clusters.",
                    "Follow the principle of least privilege for container security and IAM policies."
                ],
                "speaker_notes": "Following these best practices will lead to more robust production systems."
            },
            {
                "slide_number": 7,
                "slide_type": "content",
                "title": "Real-World Case Study",
                "subtitle": "",
                "bullet_points": [
                    "Netflix migrated to containers to handle 200+ million subscribers with zero-downtime deployments.",
                    "Spotify uses Kubernetes to manage 1,800+ microservices across multiple data centres.",
                    "Airbnb reduced deployment time from hours to minutes using CI/CD pipelines with containers.",
                    "These examples demonstrate the tangible benefits of container adoption at enterprise scale."
                ],
                "speaker_notes": "Real-world examples help illustrate the power of these technologies."
            },
            {
                "slide_number": 8,
                "slide_type": "summary",
                "title": "Key Takeaways",
                "subtitle": "",
                "bullet_points": [
                    f"{topic} is essential for modern cloud-native application deployment.",
                    "Declarative configuration and immutable infrastructure reduce errors and improve reliability.",
                    "Following best practices in security, resource management, and health checks is critical.",
                    "Real-world adoption by major companies validates the approach."
                ],
                "speaker_notes": f"To summarize, {topic} is a critical skill for any DevOps professional."
            }
        ]
    }


# ─── Module 1 mock data (3 sessions × 2 SLOs = 6 PPTs for demo) ───

MOCK_SESSIONS = [
    {
        "session_num": 1,
        "slo_1": {"text": "Explain the Docker ecosystem and container fundamentals", "topic": "Docker Ecosystem & Container Fundamentals"},
        "slo_2": {"text": "Demonstrate Docker CLI commands for image and container management", "topic": "Docker CLI & Container Management"},
    },
    {
        "session_num": 2,
        "slo_1": {"text": "Describe the DevOps toolchain and CI/CD pipeline concepts", "topic": "DevOps Toolchain & CI/CD Pipelines"},
        "slo_2": {"text": "Implement a basic CI/CD pipeline using Git and Docker", "topic": "Building CI/CD with Git & Docker"},
    },
    {
        "session_num": 3,
        "slo_1": {"text": "Explain Git essentials for version control in DevOps workflows", "topic": "Git Essentials for DevOps"},
        "slo_2": {"text": "Apply branching strategies and collaboration workflows using Git", "topic": "Git Branching & Collaboration Strategies"},
    },
]

slo_contents = []
for session in MOCK_SESSIONS:
    for slo_num in [1, 2]:
        slo_key = f"slo_{slo_num}"
        slo_info = session[slo_key]
        content = make_slo_content(session["session_num"], slo_num, slo_info["text"], slo_info["topic"])
        slo_contents.append({
            "module_num": 1,
            "session_num": session["session_num"],
            "slo_num": slo_num,
            "slo_text": slo_info["text"],
            "content": content,
        })

# Mock PDF content (what Gemini's consolidation pass would return)
mock_pdf_content = {
    "module_title": "Container Fundamentals & DevOps",
    "introduction": (
        "This module introduces the foundational concepts of containerization and DevOps practices "
        "that form the backbone of modern software delivery. Students will explore the Docker ecosystem, "
        "understand container fundamentals, learn essential DevOps toolchain components, and master "
        "Git-based version control workflows. By the end of this module, students will be able to "
        "create, manage, and deploy containerized applications using industry-standard tools and practices. "
        "The module covers 9 sessions, each with 2 Session Learning Outcomes (SLOs) aligned to the "
        "university curriculum."
    ),
    "sessions": [
        {
            "session_number": 1,
            "title": "Docker Ecosystem & Container Management",
            "slo_1_title": "Docker Ecosystem & Container Fundamentals",
            "slo_2_title": "Docker CLI & Container Management",
            "content": (
                "Containers have revolutionized how software is developed, shipped, and run in production. "
                "Docker, the most widely adopted container platform, provides a complete ecosystem for "
                "building, distributing, and running containerized applications. A Docker container packages "
                "an application with all its dependencies — libraries, runtime, system tools — into a single "
                "portable unit that runs consistently across any environment.\n\n"
                "The Docker CLI provides a powerful interface for managing images and containers. Key commands "
                "include 'docker build' for creating images from Dockerfiles, 'docker run' for starting containers, "
                "and 'docker compose' for orchestrating multi-container applications. Understanding these commands "
                "is essential for any DevOps engineer working with containerized workloads."
            )
        },
        {
            "session_number": 2,
            "title": "DevOps Toolchain & CI/CD Implementation",
            "slo_1_title": "DevOps Toolchain & CI/CD Pipelines",
            "slo_2_title": "Building CI/CD with Git & Docker",
            "content": (
                "The DevOps toolchain encompasses the set of tools and practices that enable continuous "
                "integration, continuous delivery, and continuous deployment of software applications. "
                "A well-designed CI/CD pipeline automates the build, test, and deployment process, reducing "
                "manual intervention and accelerating the software delivery lifecycle.\n\n"
                "Implementing a CI/CD pipeline with Git and Docker involves setting up automated triggers "
                "that build container images on every code commit, run automated tests, and deploy to staging "
                "or production environments. Tools like Jenkins, GitHub Actions, and AWS CodePipeline provide "
                "the orchestration layer for these automated workflows."
            )
        },
        {
            "session_number": 3,
            "title": "Git Essentials & Collaboration Workflows",
            "slo_1_title": "Git Essentials for DevOps",
            "slo_2_title": "Git Branching & Collaboration Strategies",
            "content": (
                "Git is the de facto standard for version control in modern software development and DevOps "
                "workflows. Understanding Git fundamentals — repositories, commits, branches, merges — is "
                "essential for collaborating on code and managing infrastructure as code configurations.\n\n"
                "Effective branching strategies, such as Git Flow, GitHub Flow, and trunk-based development, "
                "enable teams to work in parallel without conflicts. Pull requests, code reviews, and merge "
                "policies ensure code quality and knowledge sharing across the team. These collaboration "
                "patterns are the foundation of a healthy DevOps culture."
            )
        },
    ],
    "conclusion": (
        "This module has covered the essential building blocks of containerization and DevOps: Docker fundamentals, "
        "CI/CD pipeline design, and Git-based collaboration workflows. These skills form the foundation for the "
        "advanced topics covered in subsequent modules, including AWS services, infrastructure as code, and Kubernetes."
    ),
}

# Assemble the full module content dict (same structure as run_pipeline.py produces)
module_content = {
    "module_num": 1,
    "module_title": "Container Fundamentals & DevOps",
    "slo_contents": slo_contents,
    "pdf_content": mock_pdf_content,
}

# ─── Run the Build stage ───

output_dir = str(Path(__file__).parent / "output" / "21CSE597T")

print("=" * 60)
print("DEMO: Building files from mock data (no API key needed)")
print("=" * 60)

print(f"\nGenerating {len(slo_contents)} PPTX files for Module 1...")
ppt_files = create_module_ppts(module_content, output_dir)
print(f"\n✓ Created {len(ppt_files)} PPTX files")

print(f"\nGenerating PDF for Module 1...")
pdf_path = Path(output_dir) / "unit_1" / "unit_1_learning_material.pdf"
create_module_pdf(mock_pdf_content, 1, str(pdf_path))
print(f"✓ Created PDF: {pdf_path}")

# Also save the mock content JSON (same as what the pipeline saves)
content_json_path = Path(output_dir) / "unit_1" / "content.json"
with open(content_json_path, "w") as f:
    json.dump(module_content, f, indent=2)
print(f"✓ Saved content JSON: {content_json_path}")

print("\n" + "=" * 60)
print("OUTPUT FILES:")
print("=" * 60)
unit_dir = Path(output_dir) / "unit_1"
for f in sorted(unit_dir.rglob("*")):
    if f.is_file():
        size_kb = f.stat().st_size / 1024
        print(f"  {f.relative_to(Path(output_dir))}  ({size_kb:.1f} KB)")
