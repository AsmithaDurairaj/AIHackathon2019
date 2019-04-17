import warnings
import json
import io
import os
import copy
import subprocess
import requests

import numpy as np
import collections
from pprint import pprint
import datetime

from pyo365 import Account

from aylienapiclient import textapi

from de2 import load_from_file, DialogEngine, Context
from de2.domain import Plugin
from de2.constants import *

import sqlite3
import data




FAQ_PROBABILITY_THRESHOLD = 0.4
MAX_FAQ_RESULTS = 3
MAX_FAQ_RESULTS_FROM_SERVICE = 20

FAQ_URI = "https://qna.genesysappliedresearch.com/api/v1/models/ebe9131c88a3425b97575bd738efb571/answers"

JIRA_Check_Status_base_URI = "https://fixitai.atlassian.net/rest/api/2/issue/"

JIRA_Raise_ticket_URI = "https://fixitai.atlassian.net/rest/api/2/issue"


class search_faq(Plugin):

    def execute(self, params, context, node_id):

        context.kbot_log = {'original_query' : params['query']}

        #print("In search_faq execute")
        try:
            response = requests.post(FAQ_URI,data = json.dumps({
                                "query": params['query'],
                                "numResults": MAX_FAQ_RESULTS_FROM_SERVICE,
                                "confidenceThreshold": FAQ_PROBABILITY_THRESHOLD
                            }),headers = {  "accept": "application/json",
                        "Content-Type": "application/json" }
            )
            response.raise_for_status()
            faqAnswers = json.loads(response.text)['entities']
        except:
            print("Error while making request to the FAQ Service")
            return FAILURE, {}
        if len(faqAnswers) == 0 or faqAnswers[0]['confidence'] < FAQ_PROBABILITY_THRESHOLD:
            return FAILURE, {}
        #pprint(faqAnswers)


        answer =  faqAnswers[0]['answer']

        if len(faqAnswers) < 3:
            answer = "Solution1:\n"+faqAnswers[0]['answer'] + "\nSolution2:\n"+faqAnswers[1]['answer']

        else:
            answer = "Solution1:\n"+faqAnswers[0]['answer'] + "\nSolution2:\n"+faqAnswers[1]['answer'] + "\nSolution3:\n"+faqAnswers[2]['answer']


        #context.faq_articles = faqAnswers

        return SUCCESS, [answer]




class raise_ticket(Plugin):

    def execute(self, params, context, node_id):

        try:
            task_summary = params['query']
            payload = {
            "fields": {
                "project": {
                    "key": "TS"
                },
                "summary": task_summary,
                "issuetype": {
                    "name": "Task"
                }
            }
                }
            response = requests.post(JIRA_Raise_ticket_URI,data=json.dumps(payload),headers = { 'Content-Type': "application/json",
                                        'Authorization': "Basic bWFpbHRvcmFqZXNobWl0QGdtYWlsLmNvbTpZZ2sydkhQbUlNV0JZZ3pscW4zSzI4Rjc=",
                                        'cache-control': "no-cache",
                                'Postman-Token': "cc6cdd26-44cd-40a5-9056-7ee7f53df29a" } )


            response.raise_for_status()
            json_data = json.loads(response.text)
            ticket_id = json_data["key"]
            ticket_url = json_data["self"]
        except:
            print("Error while raising ticket")
            return FAILURE, {}

        if len(ticket_id) == 0:
            return FAILURE, {}

        #pprint(faqAnswers)
        print("Riased ticket ID \n ")
        print(json_data["key"])
        print("Ticket url is")
        print(json_data["self"])





        return SUCCESS, [ticket_id,ticket_url]



class check_ticket_status(Plugin):

    def execute(self, params, context, node_id):

        try:
            ticketid = params['ticket_id']
            print("ticket id \n")
            print(ticketid)
            url = JIRA_Check_Status_base_URI + ticketid
            print("Url is \n")
            print(url)
            response = requests.get(url,data = "",headers = {'Authorization': "Basic bWFpbHRvcmFqZXNobWl0QGdtYWlsLmNvbTpZZ2sydkhQbUlNV0JZZ3pscW4zSzI4Rjc=",
                                                                                'cache-control': "no-cache",
                                                                                'Postman-Token': "cc6cdd26-44cd-40a5-9056-7ee7f53df29a"
                                                                                })
            response.raise_for_status()
            json_data = json.loads(response.text)
            #print("response data \n")
            #print(json_data)
            status = json_data["fields"]["status"]["name"]
            print("status")
            print(status)


            #due_date = json_data["fields"]["customfield_10027"]["breachTime"]["friendly"]
            #print("due date")
            #print(due_date)
        except:
            print("Error while checking ticket status")
            return SUCCESS, ['fail','fail','fail']

        if len(status) == 0:
            return SUCCESS, ['fail','fail','fail']

        try:
            priority = json_data["fields"]["priority"]["name"]
        except:
            priority = "Low"

        try:
            assignee = json_data["fields"]["assignee"]["displayName"]
        except:
            assignee = "Prudvi"

        print("status is \n")
        print(json_data["fields"]["status"]["name"])





        return SUCCESS, [status,priority,assignee]



class update_ticket_priority(Plugin):

    def execute(self, params, context, node_id):

        try:
            ticketid = params['ticket_id']
            print("ticket id \n")
            priority = params['ticket_priority']
            print("ticket id \n")
            print(ticketid)
            url = JIRA_Check_Status_base_URI + ticketid
            print("Url is \n")
            print(url)
            payload = {"update":{"priority":[{"set":{"name" : priority}}]}}

            response = requests.put(url,data=json.dumps(payload),headers = { 'Content-Type': "application/json",
                                                    'Authorization': "Basic bWFpbHRvcmFqZXNobWl0QGdtYWlsLmNvbTpZZ2sydkhQbUlNV0JZZ3pscW4zSzI4Rjc=",
                                                    'cache-control': "no-cache",
                                                    'Postman-Token': "cc6cdd26-44cd-40a5-9056-7ee7f53df29a" } )
            response.raise_for_status()

        except:
            print("Error while updating ticket priority")
            return SUCCESS, {}





        return SUCCESS, {}




class check_asset_request_eligibility(Plugin):

    def execute(self, params, context, node_id):

        try:
            request = params['request']
            emp_id = params['employee_id']
            devices = ['mouse','keyboard','monitor','headset','headphone','docking','dock','aws','msdn','visio']
            words = request.split()
            device = 'Unknown'
            for word in words:
                if word.lower() in devices:
                    device = word.lower()
                    if (device == 'docking' or device == 'dock'):
                        device = 'dockingstation'
                    if (device == 'headphone'):
                        device = 'headset'
            conn = data.init()

            #data.createDatabase(conn)
            #data.insert(conn)
            if(device != 'Unknown'):
                eligibility = data.check_eligible(conn, device, emp_id)
                print (eligibility)

            print("Emp ID is \n")
            print(emp_id)



        except:
            print("Error while checking eligibility criteria")
            return SUCCESS, ['no',device]

        if len(eligibility) == 0:
            return SUCCESS, ['no',device]



        print("eligibility is \n")
        print(eligibility)
        print("Device is \n")
        print(device)





        return SUCCESS, [eligibility,device]

class sentiment_analysis(Plugin):

    def execute(self, params, context, node_id):



        #print("In search_faq execute")
        try:
            text = params['user_response']
            client = textapi.Client("9f33bc65", "834124f97bb37f7da8c46e53da0580b9")
            sentiment = client.Sentiment({'text': text })
            sentiment_detected = sentiment['polarity']
            print(sentiment_detected)
            if sentiment_detected == 'negative':
                priority = 'High'
            else:
                priority = 'Medium'
            print(priority)
        except:
            print("Error while performing sentiment analysis")
            return SUCCESS, ['High']
        if len(sentiment_detected) == 0 or len(priority)== 0:
            return SUCCESS, ['High']




        return SUCCESS, [priority]
