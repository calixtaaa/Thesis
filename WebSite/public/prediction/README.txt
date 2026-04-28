Put prediction outputs here so the dashboard can fetch them.

After running:
  python predictionAnalysis/run_all.py

Copy this file into this folder:
  predictionAnalysis/outputs/forecast_next_day_deep.json

Target:
  WebSite/public/prediction/forecast_next_day_deep.json

Then the dashboard Prediction Analysis will load the deep-learning forecast automatically.

Also copy:
  predictionAnalysis/outputs/insights.json
to:
  WebSite/public/prediction/insights.json

So the dashboard can show peak hours and busiest days.

