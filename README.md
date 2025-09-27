# Bring-Up AI — Streamlit MVP

Upload an IPC-356 testpoint report; parse nets; draft a bring-up procedure.
Optionally use an LLM to refine the step wording while keeping the structure deterministic.

## Run
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Optional: LLM refinement
Set your OpenAI key if you enable the toggle in the UI.
```bash
export OPENAI_API_KEY=sk-...
```
