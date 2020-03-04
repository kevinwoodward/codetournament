# codetournament

Code to run student's connect 4 agents against eachother in a seeded single elimination bracket.

Written with python 3.7.3.

# Files

- runner.py contains logic to get and put agent and seed data. Also contains connect 4 game logic.
- bracket.py contains two class implementations implementing a seeded bracket.
- canvasapi.py contains helper functions for retrieving student submissions to Canvas.

# Requirements

- apikey (file): Contains Canvas API key.
- aws_secret_access_key (file)
- aws_access_key_id (file)

# Usage 
python -B runner.py \<coursenumber\>  [--time <seconds> --delsubs -- getnone]