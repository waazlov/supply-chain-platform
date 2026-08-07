PYTHON ?= python

.PHONY: setup data pipeline test dashboard report clean

setup:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) scripts/run_pipeline.py generate

pipeline:
	$(PYTHON) scripts/run_pipeline.py all

test:
	$(PYTHON) -m pytest

dashboard:
	$(PYTHON) -m streamlit run app/app.py

report:
	$(PYTHON) scripts/run_pipeline.py report

clean:
	$(PYTHON) scripts/clean_outputs.py

