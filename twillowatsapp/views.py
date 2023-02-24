from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from twilio.twiml.messaging_response import Message, MessagingResponse
from twilio.rest import Client 
from django.http import HttpResponse
from django.utils import timezone
import openai
import os
import requests
import json

from twillowatsapp.settings import account_sid,auth_token

openai.api_key = os.getenv("openaikey",None)
#prompts
start_sequence = "\AI:"
restart_sequence = "\nHuman:"
session_prompt = f"""The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly and answers in language used in question.Today is {timezone.now().date()} {timezone.now().strftime("%A")} \n\nHuman: Hello, who are you?\nAI: I am an AI Assistant. How can I help you today?"""


def home(request):
    return render(request,'home.html')


def ask(question, chat_log=None):
    res = openai.Completion.create(
    prompt = f"{chat_log}{restart_sequence}: {question}{start_sequence}:",
    engine="text-davinci-003",
    temperature=0.9,
    max_tokens=200,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.6,
    stop=["Human:","AI:"],
    )
    return str(res['choices'][0]['text'])

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None: 
        chat_log = session_prompt 
    return f"{chat_log}{restart_sequence} {question}{start_sequence}{answer}"

def send_message(request,number):
    authorization = os.getenv("watsapp_key","EAAutF11M8dIBAG1p6V2EZAzwvsj5HDyaqrGhA7zuputoKTXTKGGugJIcfvPZB5jm4tNG9r7VKUetFGeZADnuZChpA7zzbZCrkp3qcRX6kCCZCie7JQXuBRkvAANcweRR74i0en7cKD6ZApBWuqVR2zWzBFePZCr8kU2YTD42AZCb7Ps11M8ZAD5f5vHYwVoozCB819TiepNJUMVQZDZD")
    headers = {'Authorization': f'Bearer {authorization}',"Content-Type":"application/json"}
    message = {"messaging_product": "whatsapp", "to": f"{number}", "type": "template", "template": { "name": "hello_world", "language": { "code": "en_US" } } }
    req = requests.post("https://graph.facebook.com/v15.0/108632675494612/messages",headers=headers,data=json.dumps(message))
    return JsonResponse({},status=200) 

@csrf_exempt
def re_message(request):
    chalenge = request.GET.get("hub.challenge")
    mode = request.GET.get("hub.mode")
    if mode == "subscribe":
        return HttpResponse(str(chalenge))
    else:
        if request.method == "POST":
            data = request.body
            data_dict = json.loads(data.decode("utf-8")) 
            print(request.POST,data_dict)
        else:
            print(request.POST,request.GET)
    HttpResponse(str("ok"))



@csrf_exempt
def message(request):
    if request.POST.get("Body"):
        chat_log = request.session.get("chat_log")
        if chat_log is not None:
            if len(chat_log) > 1500 or not chat_log:
                chat_log = session_prompt
        else:
            chat_log = session_prompt
        body = request.POST.get("Body")+"\n"
        answer = ask(body, chat_log)
        request.session["chat_log"] = append_interaction_to_chat_log(body, answer,chat_log)
        msg = MessagingResponse()
        msg.message(answer)
        return HttpResponse(str(msg))
    
    return HttpResponse(str("ok"))