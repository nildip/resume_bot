from flask import Flask, request, jsonify, render_template
import dialogflow
from fuzzywuzzy import fuzz
import pandas as pd
from ast import literal_eval
#import requests
#import json
import pusher

app = Flask(__name__)

# initialize Pusher
pusher_client = pusher.Pusher(app_id=<app_id>,
                              key=<key>,
                              secret=<secret>,
                              cluster=<cluster>,
                              ssl=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_response', methods=['POST'])


def get_response(user_intent, user_text):
    def get_ratio(element1, element2):
        return fuzz.token_sort_ratio(element1, element2)
    def get_bestscore_response(user_text, data):
        data['sim_score'] = 0.0
        for entity_list in data['entity']:
            data.loc[data.entity == entity_list, 'sim_score'] = max(
                [get_ratio(user_text, k) for k in literal_eval(entity_list)])
        response = data.loc[data['sim_score'].idxmax()]['response']
        return response

    db = pd.read_csv('..data\\entity.csv', encoding = "ISO-8859-1")
    user_text = user_text.lower()
    db_tmp = db[db['intent'] == user_intent]

    # trying to get response from db
    response = get_bestscore_response(user_text, db_tmp)
    if response is None:
        response = "Hey, I don't think I know the answer to that yet, however I have recorded the conversation and" \
                   "sent the query to my developer, who will get back to you soon. You may also reach him at " \
                   "mukherjee.nildip@gmail.com"
    return response


def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    if text:
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(
            session=session, query_input=query_input)

        user_intent = response.query_result.intent.display_name
        user_text = text_input.text

        dialogflow_fulfillment_text = response.query_result.fulfillment_text

        # checking if dialogflow has any proper response for user query, else call our custom function
        if dialogflow_fulfillment_text == '':
            fulfillment_text = get_response(user_intent, user_text)
        else:
            fulfillment_text = dialogflow_fulfillment_text

        return fulfillment_text


@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    project_id = <project_id>
    fulfillment_text = detect_intent_texts(project_id, "unique", message, 'en')
    response_text = {"message": fulfillment_text}

    pusher_client.trigger('resume_bot', 'new_message', {'human_message': message, 'bot_message': fulfillment_text})

    return jsonify(response_text)


# run Flask app
if __name__ == "__main__":
    app.run()
