# Local Usage Instructions

Issues appear when running a long process on the streamlit cloud, so downloading this and running it locally might be the only option to get these files generated. Either that, or splitting the npis into smaller and more manageable sections. Clone this repo and run setup using the following commands:

```
git clone 
cd payer_insights_app
python -m venv .venv        # optional but recommended
.venv\Scripts\activate      # (Windows)
pip install -r requirements.txt
streamlit run app.py
```
