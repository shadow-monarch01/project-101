"""
AI Hiring Intelligence - Skill Normalization Engine
Maps heterogeneous candidate and job skill aliases to canonical technical representations.
Provides transparent normalization metrics and alias mappings for explainable matching.
"""

from typing import Dict, List, Any, Optional, Tuple
import re

# Comprehensive canonical skill dictionary mapping aliases and variations to standard names
KNOWN_ALIASES: Dict[str, str] = {
    # Languages & Core Runtimes
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "python programming": "Python",
    "python development": "Python",
    
    "js": "JavaScript",
    "javascript": "JavaScript",
    "vanilla js": "JavaScript",
    "ecmascript": "JavaScript",
    
    "ts": "TypeScript",
    "typescript": "TypeScript",
    
    "golang": "Go",
    "go lang": "Go",
    "go": "Go",
    
    "java": "Java",
    "core java": "Java",
    "java 8": "Java",
    "java 11": "Java",
    "java 17": "Java",
    
    "cpp": "C++",
    "c++": "C++",
    "c plus plus": "C++",
    
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    ".net": ".NET",
    "dotnet": ".NET",
    
    "ruby": "Ruby",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    
    "php": "PHP",
    
    "rust": "Rust",
    
    # Databases & Storage
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgressql": "PostgreSQL",
    "pg": "PostgreSQL",
    "psql": "PostgreSQL",
    
    "mysql": "MySQL",
    "my sql": "MySQL",
    
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    
    "redis": "Redis",
    
    "sql": "SQL",
    "rdbms": "SQL",
    "relational database": "SQL",
    "relational databases": "SQL",
    "sqlite": "SQLite",
    "sqlite3": "SQLite",
    "oracle db": "Oracle",
    "oracle": "Oracle",
    
    # Web & API Frameworks
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "fastapi web framework": "FastAPI",
    
    "flask": "Flask",
    "django": "Django",
    "django rest framework": "Django REST Framework",
    "drf": "Django REST Framework",
    
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",
    
    "angular": "Angular",
    "angularjs": "Angular",
    
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",
    
    "express": "Express.js",
    "expressjs": "Express.js",
    "express.js": "Express.js",
    
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "next js": "Next.js",
    
    "rest": "REST API",
    "rest api": "REST API",
    "rest apis": "REST API",
    "restful": "REST API",
    "restful api": "REST API",
    "restful apis": "REST API",
    "restful web services": "REST API",
    
    "graphql": "GraphQL",
    "graph ql": "GraphQL",
    
    "grpc": "gRPC",
    
    "html": "HTML/CSS",
    "css": "HTML/CSS",
    "html/css": "HTML/CSS",
    "html5": "HTML/CSS",
    "css3": "HTML/CSS",
    "html css": "HTML/CSS",
    "tailwindcss": "TailwindCSS",
    "tailwind": "TailwindCSS",
    "tailwind css": "TailwindCSS",
    "bootstrap": "Bootstrap",
    
    # Cloud, DevOps & Infrastructure
    "aws": "AWS",
    "amazon web services": "AWS",
    "aws cloud": "AWS",
    
    "gcp": "Google Cloud",
    "google cloud": "Google Cloud",
    "google cloud platform": "Google Cloud",
    
    "azure": "Azure",
    "ms azure": "Azure",
    "microsoft azure": "Azure",
    
    "docker": "Docker",
    "docker containers": "Docker",
    "docker containerization": "Docker",
    "containerization": "Docker",
    
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "kube": "Kubernetes",
    
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "continuous integration": "CI/CD",
    
    "jenkins": "Jenkins",
    "github actions": "GitHub Actions",
    "git actions": "GitHub Actions",
    "gitlab ci": "GitLab CI",
    
    "terraform": "Terraform",
    "ansible": "Ansible",
    "prometheus": "Prometheus",
    "grafana": "Grafana",
    
    "linux": "Linux",
    "unix": "Linux",
    "bash": "Linux",
    "shell scripting": "Linux",
    "shell script": "Linux",
    
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "version control": "Git",
    
    "microservices": "Microservices",
    "microservice": "Microservices",
    "microservices architecture": "Microservices",
    "distributed systems": "Distributed Systems",
    
    # AI, Data Science & Machine Learning
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machine-learning": "Machine Learning",
    
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "deep-learning": "Deep Learning",
    
    "nlp": "NLP",
    "natural language processing": "NLP",
    
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    
    "ai": "Artificial Intelligence",
    "genai": "Generative AI",
    "generative ai": "Generative AI",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
    
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    
    "scikit-learn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    
    "bigquery": "BigQuery",
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "Apache Spark",
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",
    "hadoop": "Hadoop"
}

def clean_text_token(token: str) -> str:
    """Removes non-alphanumeric noise, strips punctuation, and collapses whitespace."""
    s = str(token).strip().lower()
    s = re.sub(r'[\/\-_\.]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def canonicalize_skill(skill: str) -> str:
    """
    Normalizes a skill name to its canonical form using the alias dictionary.
    If the skill is not recognized in the alias mapping, returns the cleaned title-cased string.
    """
    raw = str(skill).strip()
    if not raw:
        return ""
    
    # 1. Exact lower-case match in alias dictionary
    lower_raw = raw.lower()
    if lower_raw in KNOWN_ALIASES:
        return KNOWN_ALIASES[lower_raw]
    
    # 2. Cleaned token match in alias dictionary
    cleaned = clean_text_token(raw)
    if cleaned in KNOWN_ALIASES:
        return KNOWN_ALIASES[cleaned]
    
    # 3. Fallback: preserve original casing/standardize title case
    if len(raw) <= 3 and raw.isalpha():
        return raw.upper()
    return raw.strip()

def normalize_skill(skill: str) -> Dict[str, str]:
    """
    Returns both the original input skill string and its resolved canonical name.
    Useful for audit explanation and transparency in UI.
    """
    raw = str(skill).strip()
    canonical = canonicalize_skill(raw)
    return {
        "input": raw,
        "canonical": canonical
    }

def normalize_skills_list(skills: List[str]) -> List[Dict[str, str]]:
    """Normalizes a list of skills, returning list of {input, canonical} pairs."""
    return [normalize_skill(s) for s in skills if str(s).strip()]

def get_canonical_skills(skills: List[str]) -> List[str]:
    """Returns deduplicated list of canonical skill names."""
    seen = set()
    result = []
    for s in skills:
        canon = canonicalize_skill(s)
        if canon and canon not in seen:
            seen.add(canon)
            result.append(canon)
    return result
