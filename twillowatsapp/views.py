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
    authorization = os.getenv("watsapp_key",None)
    headers = {'Authorization': f'Bearer {authorization}',"Content-Type":"application/json"}
    message = {"messaging_product": "whatsapp", "to": f"{number}", "type": "template", "template": { "name": "hello_world", "language": { "code": "en_US" } } }
    req = requests.post("https://graph.facebook.com/v15.0/108632675494612/messages",headers=headers,data=json.dumps(message))
    return JsonResponse({},status=200) 

def send_ai_message(request,number,message):
    chat_log = request.session.get("chat_log")
    if chat_log is not None:
        if len(chat_log) > 1500 or not chat_log:
            chat_log = session_prompt
    else:
        chat_log = session_prompt
    body = request.POST.get("Body")+"\n"
    answer = ask(body, chat_log)
    message = {
      "messaging_product": "whatsapp",
      "recipient_type": "individual",
      "to": f"{number}",
      "type": "text",
      "text": {
        "preview_url": False,
        "body": f"{answer}"
        }
    }
    authorization = os.getenv("watsapp_key",None)
    headers = {'Authorization': f'Bearer {authorization}',"Content-Type":"application/json"}
    req = requests.post("https://graph.facebook.com/v15.0/108632675494612/messages",headers=headers,data=json.dumps(message))

    

@csrf_exempt
def re_message(request):
    chalenge = request.GET.get("hub.challenge")
    mode = request.GET.get("hub.mode")
    if mode == "subscribe":
        return HttpResponse(str(chalenge))
    else:
        if request.method == "POST":
            data = request.body
            data_dict = json.loads(data.decode("utf-8"))['entry'][0]['changes'][0]['value']
            if data_dict.get('messages',None):
                data_dict = data_dict['messages'][0]
                number = data_dict['from']
                message = data_dict['text']['body']
                send_ai_message(request,number,message)
            print(request.POST,data_dict,message)
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