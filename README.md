KBC - AI Trivia Game
A KBC-style trivia quiz game with AI-generated questions using Google's Gemini API. Questions are freshly generated per playthrough based on your chosen domain, with difficulty and regional focus automatically escalating through 5 levels.
Features
AI-Generated Questions: Fresh questions every game via Gemini API
5 Difficulty Levels: From medium (West Bengal) to extreme (worldwide)
7 Domains + Mixed Mode: Science, History, Geography, Sports, Entertainment, Technology, Literature
Checkpoint Scoring: Safe amounts at each level
Timer: Per-level time limits
Badges: Earn badges based on performance
Leaderboard: Local score tracking
Two Versions: Terminal and Streamlit web app
Quick Start

1. Setup
   bash

# Create virtual environment

python -m venv venv

# Activate (Linux/Mac)

source venv/bin/activate

# Activate (Windows)

venv\Scripts\activate

# Install dependencies

pip install -r requirements.txt 2. Get a Free Gemini API Key
Go to Google AI Studio
Sign in with your Google account
Click "Create API Key"
Copy your key 3. Configure API Key
Option A: Environment Variable (Recommended)
bash
export GEMINI_API_KEY="your_key_here" # Linux/Mac
set GEMINI_API_KEY=your_key_here # Windows CMD
$env:GEMINI_API_KEY="your_key_here" # Windows PowerShell
Option B: .env File
bash
cp .env.example .env

# Edit .env and add your key

Option C: Streamlit Secrets (for deployment)
Add GEMINI_API_KEY in Streamlit Cloud dashboard 4. Run Terminal Version
bash
python terminal_game.py 5. Run Streamlit Version (Local)
bash
streamlit run app.py
Game Rules
Table
Level Questions Time Safe Amount Wrong Answer Quit/Timeout
1 2 30s ₹0 Reset to ₹0 Reset to ₹0
2 2 45s ₹500 Keep ₹500 Keep ₹500
3 3 60s ₹1,300 Reset to ₹1,300 Keep progress
4 4 60s ₹2,500 Keep progress Keep progress
5 3 90s ₹4,000 Reset to ₹0 Keep ₹4,000
Maximum Prize: ₹7,000
Badges
🏆 Crorepati - Complete all 5 levels perfectly
🥇 Diamond - Reach Level 5
🥈 Gold - Reach Level 4
🥉 Silver - Reach Level 3
⭐ Bronze - Reach Level 2
Project Structure
plain
kbc_game/
├── game_logic.py # Core game state & scoring (tested)
├── questions.py # AI question generation + hardcoded fallback
├── terminal_game.py # Command-line version
├── app.py # Streamlit web version
├── requirements.txt # Python dependencies
├── .env.example # API key template
├── .gitignore # Git ignore rules
└── README.md # This file
No API Key? No Problem!
If you don't set a Gemini API key, the game automatically falls back to a built-in set of 14 hardcoded questions. The game works perfectly without any API calls.
Deploy to Streamlit Cloud
Push this repo to GitHub (make sure .env is in .gitignore!)
Go to Streamlit Community Cloud
Connect your GitHub repo
Add GEMINI_API_KEY as a secret in the dashboard
Deploy and share your link!
Troubleshooting
"404 models/gemini-1.5-flash is not found"
The old model name gemini-1.5-flash is deprecated. This project now uses:
Primary: gemini-2.5-flash (recommended free-tier model)
Fallback: gemini-2.5-flash-lite → gemini-2.0-flash
If you see 404 errors, the code automatically tries the next model in the chain.
"google-generativeai not installed"
The old SDK google-generativeai is deprecated as of November 2025.
This project uses the new google-genai SDK.
bash
License
Personal / Portfolio Project
