OFFER RANKER SYSTEM

What it is: a small machine-learning web service. You send it four facts about a customer (age, months as a customer, monthly spend, number of support tickets) and it answers with the probability that the customer would accept an upsell offer, plus a yes/no label (yes when the probability is 50 percent or more). It is built with FastAPI and scikit-learn, packaged with Docker, and has Terraform and GitHub workflows for putting it on Google Cloud Run.

What is NOT local: the Google Cloud deployment. That needs your own GCP project and secrets. Running and testing the service on your computer needs none of that.

What you need: Python 3.11 or 3.12 (it does not install on 3.14), Docker only if you want the container, and port 8080 free. You do not need a GCP account, Terraform or gcloud to run it locally.

How to run it:
1. Go into the api folder, create a virtual environment, activate it, and run: pip install -r requirements.txt
2. Run: make run-local   (serves at http://localhost:8080)
3. Check it: curl http://localhost:8080/health
4. Ask for a prediction: curl -X POST http://localhost:8080/predict -H "Content-Type: application/json" -d '{"age":30,"tenure_months":12,"monthly_spend":123.4,"num_support_tickets":1}'
Container: docker build -t offer-ranker-api ./api, then docker run --rm -p 8080:8080 offer-ranker-api.
If port 8080 is taken: PORT=8090 make run-local, or for Docker use -p 127.0.0.1::8080 which picks a free port (docker port NAME tells you which). Be careful: if something else is on 8080 you will get that other program's error page, not this service's answers.

What it does:
- /health says ok if the model loaded, and returns an error if it did not.
- /predict returns the probability, the yes/no label and a request id. Bad input (negative age, text instead of a number, extra fields) is rejected with a 422 error.
- /metrics shows simple counters: total requests, prediction requests, average speed and the time of the last prediction.
None of the three requires a login.

Tests: from the api folder run pytest -q. There are 10 tests covering the API, model loading and input checking. They need no outside services. Warning: running the tests rewrites the committed model file api/models/offer_model.joblib, so restore it with git restore afterwards. On pull requests GitHub runs the tests, a Docker build and a secrets scan on free machines. The Google Cloud workflows (ci, cd, cd_dispatch, ci-cd, destroy) need secrets and do not run on pull requests.

Where things are: api/app is the service, api/tests the tests, api/scripts has the training script and a smoke-test script, api/infrastructure is Terraform, dq is a data-quality checker driven by a YAML rules file, training holds a notebook, planned-features holds ideas that are not built.

Design choices: input is checked strictly so the string "30" is refused instead of silently turned into a number. A tiny trained model file is committed so the container starts without training. Deploy workflows are kept apart from pull-request checks so a pull request never needs cloud credentials.
