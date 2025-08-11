    # HYDRA-Lite MVP - Coastal Green Ammonia Hub


    ## What's included


    - `lcoh.py` : Calculation engine for LCOH and LCOA (INR + USD)

    - `app.py` : Streamlit UI to run the model and download CSV outputs

    - `requirements.txt` : Python requirements


    ## How to run locally


    1. Install Python 3.10+

    2. Create a venv and activate it:

       ```bash

       python -m venv venv

       source venv/bin/activate  # Linux/Mac

       venv\Scripts\activate    # Windows

       ```

    3. Install requirements:


       ```bash

       pip install -r requirements.txt
       ```


    4. Run the app:


       ```bash

       streamlit run app.py
       ```


    ## Deploy to Streamlit Cloud


    1. Create a GitHub repo and push these files.

    2. Sign in to https://streamlit.io/cloud and connect your GitHub.

    3. Select the repo and deploy.


    ## Notes


    - Defaults are editable in the Streamlit sidebar.
- This is an MVP. We can add scenario compare, Sankey diagrams, PDF export, and improved UX next.

