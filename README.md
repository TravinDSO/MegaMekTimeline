Application will consolidate SARNA timelines, the Megamek news, and any custom timelines placed in the megamek_timelines folder.

Afterwards, the consolidated timeline can be added to the docs folder (plus any additional XML, TXT, CSV, or PDF files) for indexing and embedding.
_note: you must have access to an OpenAI or Azure API key for this to function_

Once indexed and embedded, the application will allow users to use GPT type prompting to ask questions about the Battletech universe and timeline.
_note: you must have access to an OpenAI or Azure API key for this to function_

Installation
------------

Install Python 3.7 or later (https://www.python.org/downloads/)

Install Git (https://git-scm.com/)

Clone the repository with `git clone https://github.com/TravinDSO/MegaMekTimeline`

Create a virtual environment `python -m venv venv`

Activate the virtual environment `source venv/bin/activate` (Linux) or `venv\Scripts\activate` (Windows)

Install the required packages with `pip install -r requirements.txt`

_note: you must have access to an OpenAI or Azure API key the indexing and questioning to work_
To obtain your OPENAI_API_KEY, sign up for an account at https://platform.openai.com/signup/
Then, go to the API Keys section in your account to find your API key.
Open the environment.env and add your key to the OPENAI_API_KEY="" variable

Running the application
-----------------------
run the main.py file using `python main.py`
