# Setup

```powershell
python scripts/download_data.py
python scripts/preprocess_data.py
python scripts/train_models.py
python -m unittest discover -s tests
uvicorn api.main:app --reload
streamlit run dashboard/app.py
```
