\# NewsIQ 📰



\*\*AI-Powered News Intelligence Platform\*\*



NewsIQ is a full-stack AI news platform that fetches live news, lets users search and explore articles by category, and generates concise AI-powered summaries.



The platform uses a React frontend, FastAPI backend, PostgreSQL database, NewsAPI, and AI-powered summarization with Gemini and Groq fallback.



\## 🚀 Live Demo



https://news-iq-rho.vercel.app/



\## 📂 GitHub



https://github.com/jaiswalritesh150-art/News\_IQ



\---



\## ✨ Features



\- 📰 Fetch live news from NewsAPI

\- 🔎 Search news by keywords

\- 🗂️ Browse news by categories

\- 🤖 AI-powered article summarization

\- ⚡ Gemini as the primary AI provider

\- 🔄 Groq fallback when Gemini is unavailable

\- 💾 PostgreSQL database for persistent storage

\- 🧠 Persistent summary caching

\- 🚀 REST APIs with FastAPI

\- 📊 Database statistics

\- 🎨 Responsive React frontend

\- ☁️ Production deployment with Vercel and Render



\---



\## 🏗️ Architecture



```text

&#x20;                   ┌─────────────────────┐

&#x20;                   │      NewsAPI        │

&#x20;                   │   Live News Data    │

&#x20;                   └──────────┬──────────┘

&#x20;                              │

&#x20;                              ▼

┌─────────────────┐     ┌─────────────────────┐

│  React Frontend │────▶│   FastAPI Backend   │

│     Vercel      │     │       Render        │

└─────────────────┘     └──────────┬──────────┘

&#x20;                                  │

&#x20;                    ┌─────────────┴─────────────┐

&#x20;                    │                           │

&#x20;                    ▼                           ▼

&#x20;            ┌──────────────┐            ┌──────────────┐

&#x20;            │ PostgreSQL   │            │ AI Providers │

&#x20;            │   Database   │            │              │

&#x20;            │              │            │ Gemini       │

&#x20;            │ Articles     │            │      ↓       │

&#x20;            │ Summaries    │            │ Groq Fallback│

&#x20;            └──────────────┘            └──────────────┘

