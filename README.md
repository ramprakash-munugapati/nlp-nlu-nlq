# nlp-nlu-nlq
Natural Language Processing, Understanding and Query

## Running the spaCy example

Install spaCy and its English language model using the same Python interpreter:

```powershell
python -m pip install spacy
python -m spacy download en_core_web_sm
python .\nlq_level2.py
```

## Running the LM Studio example

In LM Studio, load `liquid/lfm2.5-1.2b` and start the local server (the default
address is `http://localhost:1234`). Then run:

```powershell
lms load liquid/lfm2.5-1.2b
lms server start
python -m pip install requests
python .\nlq_level3.py
```

The script uses `http://localhost:1234/v1` and `liquid/lfm2.5-1.2b` by default.
Set `LM_STUDIO_BASE_URL` or `LM_STUDIO_MODEL` if your server address or loaded
model identifier differs. Generated SQL is restricted to read-only queries. If
LM Studio terminates the model during generation, check its logs for the cause.
