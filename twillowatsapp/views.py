from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from twilio.twiml.messaging_response import Message, MessagingResponse
from twilio.rest import Client 
from django.http import HttpResponse
from django.utils import timezone
import openai
import os

from twillowatsapp.settings import account_sid,auth_token

openai.api_key = os.getenv("openaikey",None)
#prompts
start_sequence = "\AI:"
restart_sequence = "\nHuman:"
session_prompt = f"""The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly and answers in language used in question.Today is {timezone.now().date()} {timezone.now().strftime("%A")} \n\nHuman: Hello, who are you?\nAI: I am an AI Assistant. How can I help you today?"""


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

def send_message(request):
    client = Client(account_sid, auth_token) 
    message = client.messages.create( 
                                from_='whatsapp:+14155238886',  
                                body='Your appointment is coming up on July 21 at 3PM',      
                                to='whatsapp:+923129601966' 
                            ) 
    
    return JsonResponse({},status=200)



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