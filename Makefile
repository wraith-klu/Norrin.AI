install:
	python -m pip install -r requirements.txt

test:
	python -m unittest discover -s tests

train:
	python scripts/train_models.py

api:
	uvicorn api.main:app --reload

dashboard:
	streamlit run dashboard/app.py

preprocess:
	python scripts/preprocess_data.py
