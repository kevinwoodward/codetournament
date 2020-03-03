import importlib
import requests as r
from pathlib import Path



def import_agent(path, player_num):
    '''
    takes path in the form of:
        submissions/<ucsc-alias>/Player.py
        Note the .py at the end.
        
    '''
    player_module = importlib.import_module(path.split(".")[0].replace("/","."))
    agent = player_module.AIPlayer(player_num)
    return agent

def get_submissions(course_num, assignment_num, api_token, dest_path="./submissions"):
    '''
    takes in course/assignment number and canvas api token
        stores them in the following directory structure:
            submissions/
                |-student1/
                    |-<submitted file>
                |-student2/
                    |-<submitted file>
                |-student3/
                    |-<submitted file>
                ...
    '''
    
    users_url = f'https://canvas.ucsc.edu/api/v1/courses/{course_num}/users?per_page=100'
    submissions_url = f'https://canvas.ucsc.edu/api/v1/courses/{course_num}/assignments/{assignment_num}/submissions?per_page=100'
    headers = {"Authorization":f'Bearer {api_token}'}
    resp_users = r.get(users_url, headers=headers)
    user_dict = {x["id"]:x["email"] for x in resp_users.json()}
    resp_sub = r.get(submissions_url, headers=headers)
    for item in resp_sub.json():
        try:
            if item["missing"] or item["user_id"] not in user_dict.keys() or 'attachments' not in item.keys():
                continue
            user = user_dict[item["user_id"]].split("@")[0]
            path = Path(f'{dest_path}/{user}')
            path.mkdir(parents=True, exist_ok=True)
            attachment = item['attachments'][-1]
            resp = r.get(attachment["url"], headers=headers)
            with open(path / attachment["filename"], 'wb') as f:
                f.write(resp.content)
        except Exception as e:
            print(e)
            raise e

