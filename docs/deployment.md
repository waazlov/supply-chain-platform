# Deployment

## Local

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py all
streamlit run app/app.py
```

## Docker

```bash
docker build -t supply-chain-intelligence .
docker run --rm -p 8501:8501 -v "$PWD/data:/app/data" -v "$PWD/database:/app/database" -v "$PWD/models:/app/models" -v "$PWD/reports:/app/reports" supply-chain-intelligence
```

## GitHub Actions

`ci.yml` runs dependency installation, linting, tests, a small pipeline integration check, and dashboard import validation. `scheduled_pipeline.yml` runs the full pipeline on a schedule and stores reports as artifacts.

## Production Considerations

Use managed secrets for source credentials, replace synthetic generation with read-only data extracts, pin dependency hashes, add model monitoring, and protect dashboard access with organization authentication.

