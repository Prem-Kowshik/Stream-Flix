# wikiflix
This project is to create an alternate version of wikiflix using python, streamlit and fastapi.
Using this application you can watch and browse for any public domain movie available on wikimedia commons

There are three files-
1. response_testing.py : gets the responses from wikimedia commons using responses module
2. api.py : uses fastapi for backend
3. streamlit_frontend.py : Frontend for the project, made using streamlit in python

To run the project-
1. On the terminal, first run uvicorn api:app --reload
2. On another instance of the terminal, run streamlit run streamlit_frontend.py

