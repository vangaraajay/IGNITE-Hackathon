# LoRa PCB Test Procedure Generator

Created for the **UF Ignite Hackathon** event.

## What it is

We (Tyler Dang, Archit Namboodiri, and Ajay Vangara) made this project as part of the UF Ignite Hackathon by Aeronix. It's a AI-Powered PCB test plan generator that uses LLM integration to take in files and generate a PCB Test plan procedure, something that currently takes electrical engineers hours to do!

**Key Features:**
- Processes multiple file formats (DOCX, XML, XLSX, PNG, TXT)
- Generates step-by-step testing procedures
- Creates voltage guardrail tests with tolerances
- Includes component verification and signal testing
- Outputs formatted DOCX documents ready for engineering use

**Built with:** Streamlit, OpenAI API, Python

## Demo Video

Here's a demo video of our project explaining the project and stack: https://www.youtube.com/watch?v=6psfQiA6fKk

## Setup

1. Install dependencies: `pip install streamlit pandas python-docx pillow python-dotenv openai`
2. Create `.env` file with `OPENAI_API_KEY=your_key_here`
3. Run: `streamlit run streamlit_app.py`