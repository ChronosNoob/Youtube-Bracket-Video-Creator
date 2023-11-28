import os
from apiclient import discovery
from httplib2 import Http
from oauth2client import client, file, tools

from typing import Dict, List, Any, Tuple, Union

def build_service(scopes: str, discovery_doc: str, token_file: str):
    store = file.Storage(token_file)
    creds = store.get()

    if not creds or creds.invalid:
        secrets_file_name = [item for item in os.listdir('.') if 'client_secret' in item][0] # TODO are there multiple secrets files for forms + Youtube how to know which is which?
        flow = client.flow_from_clientsecrets(secrets_file_name, scopes)
        creds = tools.run_flow(flow, store)

    return discovery.build('forms', 'v1', http=creds.authorize(Http()), discoveryServiceUrl=discovery_doc)#, static_discovery=False)

def form_response(form_id: str) -> List[Any]:
    # https://developers.google.com/forms/api/guides/retrieve-forms-responses

    SCOPES = "https://www.googleapis.com/auth/forms.responses.readonly"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    TOKEN_FILE = 'oauth_form_response.json'
    service = build_service(SCOPES, DISCOVERY_DOC, TOKEN_FILE)

    # Prints the responses of your specified form:

    #result = service.forms().responses().list(formId=form_id, pageSize=5000).execute()

    has_next = True
    token = None
    responses = []
    result = {}

    while has_next: # TODO check that it goes through all pages
        if token:
            result = service.forms().responses().list(formId=form_id, pageSize=5000, pageToken=token).execute()
        else:
            result = service.forms().responses().list(formId=form_id, pageSize=5000).execute()
        responses.extend(result['responses'])

        if 'nextPageToken' not in result or result['nextPageToken']:
            has_next = False
        else:
            token = result['nextPageToken']

    return responses

def compile_results(responses) -> Union[List[str], Dict[str, int]]:
    # create appropriate amount of dict lookup tables
    question_response_counts: List[Dict[str, int]] = [{} for _ in enumerate(responses[0]['answers'].keys())]
    # insert values into dicts
    for item in responses:
        for i,(_,value) in enumerate(item['answers'].items()):
            vote_choice = value['textAnswers']['answers'][0]['value']
            print(value['textAnswers']['answers'][0]['value'])
            if vote_choice in question_response_counts[i]:
                question_response_counts[i][vote_choice] += 1
            else:
                question_response_counts[i][vote_choice] = 1

    print(question_response_counts)
    # returns winner based on question
    return [max(counts, key=counts.get) for counts in question_response_counts], question_response_counts[0]

def create_question(options: List[str], index: int) -> Dict[str, Any]:
    return { "createItem": {
            "item": {
                "title": "Which is better?",
                "questionItem": {
                    "question": {
                        "required": True,
                        "choiceQuestion": {
                            "type": "RADIO",
                            "options": [{"value": item} for item in options],
                            "shuffle": False,
                        }
                    }
                },
            },
            "location": {
                "index": index,
            }
        }
    }


def make_form(option_values: List[List[str]]) -> Tuple[str, str]:
    ''' ORIGINAL DICT form:

    {'formId': '1XqufYZKpcu-NSV3ihGDpER5-MozASIE1Tl4Sj_U-DCs', 'info': {'title': 'Test Form', 'documentTitle': 'Untitled form'}, 'revisionId': '00000004', 'responderUri': 'https://docs.google.com/forms/d/e/1FAIpQLSevrC9b-MeyOWXDb415uUJqrvmmuBbXO91HeuVMlVY62dEEqA/viewform', 'items': [{'itemId': '0622d9a2', 'title': 'TEST', 'questionItem': {'question': {'questionId': '65f99e20', 'required': True, 'choiceQuestion': {'type': 'RADIO', 'options': [{'value': 'Yes'}, {'value': 'No'}, {'value': 'Other'}]}}}}]}
    '''
    SCOPES = "https://www.googleapis.com/auth/forms.body"
    DISCOVERY_DOC = "https://forms.googleapis.com/$discovery/rest?version=v1"

    TOKEN_FILE = 'oauth_create_form.json'
    form_service = build_service(SCOPES, DISCOVERY_DOC, TOKEN_FILE)

    NEW_FORM = {
        "info": {
            "title": "Test Form",
        }
    }

    NEW_QUESTION = {
        "requests": [create_question(item, index) for index,item in enumerate(option_values)]
    }

    result = form_service.forms().create(body=NEW_FORM).execute()

    question_setting = form_service.forms().batchUpdate(formId=result['formId'], body=NEW_QUESTION).execute()

    get_result = form_service.forms().get(formId=result['formId']).execute()
    return get_result['formId'], get_result['responderUri']

if __name__ == '__main__':
    # for testing purposes and the main functions
    #print(make_form([['upload', 'edit', 'review'], ['test1', 'test2', 'test3']]))
    print(compile_results(form_response('1XqufYZKpcu-NSV3ihGDpER5-MozASIE1Tl4Sj_U-DCs'))) # formId and not the form link

