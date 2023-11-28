import os
import time
import datetime
from typing import Tuple, List
import argparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

# local files
import bracket
import gforms
import upload_video
import settings

def build_service(scopes: str, discovery_doc: str, token_file: str):
    store = file.Storage(token_file)
    creds = store.get()

    if not creds or creds.invalid:
        secrets_file_name = [item for item in os.listdir('.') if 'client_secret' in item][0]
        flow = client.flow_from_clientsecrets(secrets_file_name, scopes)
        creds = tools.run_flow(flow, store)

    return discovery.build('youtube', 'v3', http=creds.authorize(Http()), discoveryServiceUrl=discovery_doc)#, static_discovery=False)

def get_video_description(video_link: str) -> str:
    SCOPES = "https://www.googleapis.com/auth/youtube.force-ssl"
    DISCOVERY_DOC = "https://youtube.googleapis.com/$discovery/rest?version=v3"

    TOKEN_FILE = 'oauth_video_lookup.json'
    service = build_service(SCOPES, DISCOVERY_DOC, TOKEN_FILE)
    video_id: str = video_link.split('=')[-1]
    video_stats = service.videos().list(part="snippet,contentDetails", id=video_id).execute()
    return video_stats['items'][0]['snippet']['description']

def get_last_upload() -> Tuple[str, str]: # TODO ASSUMING A VIDEOS CHANNEL AND NOT SHORTS ONLY
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    os.environ['WDM_LOG_LEVEL'] = "0" # to remove startup logs

    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    driver.get(f'{settings.channel_link}/videos')
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    title_id: str = 'video-title-link' if '/@' in settings.channel_link else 'video-title'
    content = soup.find_all('a', {'id': title_id}, href=True)
    if len(content) == 0:
        content = soup.find_all('a', {'id': 'video-title-link'}, href=True)
    driver.close()

    return content[0]['href'], content[0]['title']

def make_video(competitors: List[List[str]], winners: str, winner_voting: Dict[str, int], round_number: int, competitors_left: int) -> str:
    #raise NotImplementedError
    #return # path to the file (if in a different directory) or the file name (if in the current working directory)
    return 'videoplayback.mp4' # TODO ONLY FOR TESTING PURPOSES

def video_upload(file_name: str, title: str, description: str, upload_time: str = None) -> None:
    args = argparse.Namespace()
    args.auth_host_name = 'localhost' 
    args.auth_host_port = [8080, 8090]
    args.category = '22'
    args.description = description
    args.file = file_name
    args.keywords = f'verus,{",".join(title.split())}'
    args.logging_level = 'ERROR'
    args.noauth_local_webserver = False
    args.privacyStatus = 'public' # for testing use 'private
    if upload_time:
        # https://www.w3.org/TR/NOTE-datetime # upload_time formatting
        args.publishAt = upload_time # if setting --> then privacyStatus must be private
        args.privacyStatus = 'private'
    args.selfDeclaredMadeForKids = False
    args.title = title
    
    upload_video.main(args)

def convert_upload_time(month: int, day: int, hour: int, minute: int) -> str:
    # https://note.nkmk.me/en/python-datetime-isoformat-fromisoformat/#:~:text=To%20convert%20date%20and%20time,%2C%20time%20%2C%20and%20datetime%20objects.
    year = datetime.date.today().year # gets the current year

    upload_date = datetime.datetime(year, month, day, hour, minute)
    # 2023-04-01 05:00
    return upload_date.isoformat()

def main():
    try:
        last_upload_link, last_upload_title = get_last_upload()
    except IndexError:
        last_upload_link, last_upload_title = None, None

    competitors: List[List[str]] = []
    winners: List[str] = []
    winner_voting: Dict[str, int] = {}
    round_number: int = 0
    competitors_left: int = -1
    if 'WINNER' in last_upload_title or not last_upload_title:
        competitors, round_number, competitors_left = bracket.create_new_bracket()
    else:
        video_description = get_video_description(last_upload_link)
        form_id: str = video_description.split('\n')[-1] # get the final id for google forms
        winners, winner_voting = gforms.compile_results(gforms.form_response(form_id)) # '1XqufYZKpcu-NSV3ihGDpER5-MozASIE1Tl4Sj_U-DCs'
        competitors, round_number, competitors_left = bracket.get_new_competitor_pair(winners[0])

    video_path: str = make_video(competitors, winners[0], winner_voting, round_number, competitors_left) # return file name

    # create title and description for uploading
    video_title: str = ''
    form_url: str = ''
    form_id: str = ''
    if len(competitors[0]) == 1:
        video_title = 'Tournament WINNER Declared'
    else:
        video_title = f'Tournament Stage: {competitors[0]} vs {competitors[1]}' # TODO how to name videos
        form_url, form_id = gforms.make_form(competitors)
    description: str = f'{form_url}\n\n{form_id}'

    MONTH: int = 10
    DAY: int = 10
    HOUR: int = 12 # this value goes to 24 (for AM and PM) NOT a 12 hour clock # if set to -1 then will auto publish
    MINUTE: int = 0
    upload_time: str = convert_upload_time(MONTH, DAY, HOUR, MINUTE) if HOUR != -1 else None
    video_upload(video_path, video_title, description, upload_time)


if __name__ == '__main__':
    main()


"""#bracket.py float
percentage
round/matchup number
cronjobs
scheduling api"""