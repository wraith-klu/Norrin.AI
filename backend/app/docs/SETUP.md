# Setup

```powershell
python -m app.scripts.seed
python -m app.scripts.preprocess
python -m app.scripts.train
python -m pytest
uvicorn app.main:app --reload
streamlit run app/frontend/app.py
```
