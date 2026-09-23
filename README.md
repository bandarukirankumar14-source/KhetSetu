# KhetSetu

KhetSetu is a two-sided AgriTech marketplace prototype that helps farmers decide what to grow, discover nearby buyer demand, and sell directly to verified retailers. It is designed around the full crop journey:

**Demand -> crop decision -> cultivation -> harvest -> buyer -> delivery -> payment**

The current prototype is a polished farmer console backed by Flask and SQLite. It includes:

- A farmer dashboard with farm summary, market pulse, buyer demand, price watch, and farm score.
- Seeded buyer requirements from retailers in Hyderabad, Secunderabad, and Gachibowli.
- Crop recommendations based on soil, irrigation, season, and nearby demand.
- A produce listing flow that writes a new listing to SQLite.
- An offer flow where a farmer responds to a buyer requirement.
- Responsive mobile behavior and a simple mobile navigation drawer.
- A health endpoint at `/healthz` for deployment checks.

The data is intentionally demo data. Prices, demand, crop recommendations, payment protection, quality grading, KYC, and logistics integrations should be connected to real providers before the product is used for commercial decisions.

## Run locally

Python 3.11+ is recommended. On Windows, the Python launcher can be used if `python` is not on PATH:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`. The first run creates `khetsetu.db` and seeds the demo farmer, listings, and buyer demand.

## Try both roles

The landing screen lets you register a new account or sign in as either role. For a quick demo, use:

- Farmer: `farmer@khetsetu.demo` / `farmer123`
- Retailer: `retailer@khetsetu.demo` / `retailer123`

Farmers get crop recommendations, local buyer demand, produce listings, and offer submission. Retailers get direct farmer produce, requirement posting, and incoming offer review. The API enforces these boundaries server-side, not only in the browser.

## Deploy on AWS free tier

For a low-cost prototype, use AWS Elastic Beanstalk with the Python platform and a single EC2 instance. AWS free-tier eligibility and limits depend on the account age and region, so check the current AWS pricing page before deploying. Do not treat SQLite on a single instance as a production database: instance replacement or scaling can lose local data.

1. Install and configure the AWS CLI and the Elastic Beanstalk CLI.
2. From this folder, run `eb init` and select a nearby AWS region and the Python platform.
3. Create a single-instance environment with `eb create khetsetu-demo --single`.
4. Open the deployed URL with `eb open`.
5. Check the deployment with `curl https://YOUR-URL/healthz`.

The included `Procfile`, `runtime.txt`, `requirements.txt`, and `healthz` route are already set up for this deployment. For a real launch, move the database to Amazon RDS or a managed PostgreSQL service, store uploads in S3, add authentication and KYC, and put secrets in Elastic Beanstalk environment properties rather than source code.

## Suggested next milestones

1. Add farmer and buyer authentication with phone OTP.
2. Add a buyer dashboard for posting requirements and accepting offers.
3. Add weather, mandi price, crop-calendar, and local-language/voice integrations.
4. Add order, logistics, payment, dispute, and two-sided reputation workflows.
5. Replace demo recommendations with a documented, explainable decision-support model.