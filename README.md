# CareerRadar AI 🚀

**An AI-powered career analysis platform that helps users identify skill gaps, build personalized learning roadmaps, and discover relevant job opportunities.**

## 📌 Overview

CareerRadar AI helps job seekers understand how their current skills align with the requirements of their target roles. It analyzes job descriptions, identifies matching skills and skill gaps, and provides guidance to support career development.

## ✨ Features

- **Skill Analysis:** Compare user skills with job requirements.
- **Skill Gap Detection:** Identify skills that need improvement.
- **AI-Powered Learning Roadmaps:** Generate personalized learning recommendations.
- **Job Search:** Discover relevant job opportunities.
- **Analysis History:** Save and revisit previous analyses.
- **Career Chat:** Interact with an AI assistant for career-related guidance.

## 🛠️ Tech Stack

- **Python** — Core application logic
- **Gradio** — User interface
- **Groq API** — AI-powered analysis and responses
- **SQLite** — Local data storage
- **Adzuna API** — Job search integration, if enabled in the current configuration

## 📂 Project Structure

```text
CareerRadar-AI/
├── agent/
│   ├── skill_analyzer.py
│   ├── job_analyzer.py
│   ├── roadmap_generator.py
│   ├── career_agent.py
│   └── chat_agent.py
├── database/
│   └── db.py
├── servicer/
│   └── llm_service.py
├── tool/
│   └── job_search.py
├── app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The structure above should be adjusted if your actual filenames differ.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd CareerRadar-AI
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository's HTTPS URL.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.example` as a template, then add your own API credentials.

Required credentials depend on the integrations enabled in your configuration, such as Groq and Adzuna.

**Never commit your `.env` file or expose API keys publicly.**

### 5. Run the application

```bash
python app.py
```

Open the local URL displayed in the terminal.

## 🔐 Security

- API credentials are stored in environment variables.
- `.env` should be excluded from Git using `.gitignore`.
- Each user should configure their own API keys locally.

## 🎯 Project Goal

CareerRadar AI aims to make career planning more practical by connecting skill assessment, personalized learning guidance, and job discovery in one application.

## 👨‍💻 Author

Add your name and professional links here.

## 📄 License

No license has been selected yet. Add a license if you decide to distribute the project under specific terms.
