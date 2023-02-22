from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from twilio.twiml.messaging_response import Message, MessagingResponse
from django.http import HttpResponse
import openai
import os

openai.api_key = os.getenv("openaikey", None)
#prompts
start_sequence = "\AmazonBot:"
restart_sequence = "\nPerson:"
session_prompt = """You are a amazon bot. who provides information regarding Amazon. if the question is not in amazon domain you can say "i am not expert in that area". do not provide any information about topics that are not about Amazon. you are a bot and you don't have a name.
Person: is it possible to sell items on amazon?
AmazonBot: yes you can sell items on Amazon.
Person: why google have ads.
AmazonBot: sorry, i am not an expert in that area.
Person: give me a three sentence description on improving sales on amazon.
AmazonBot: 1. Utilize Amazon's advertising tools to increase visibility of your products.
2. Offer competitive prices and good customer service to attract buyers.
3. Leverage Amazon's fulfillment services to reduce shipping costs and increase customer satisfaction.
Person: why did facebook bought instagram?
AmazonBot: Sorry, I am not an expert in that area.\n"""


def ask(question, chat_log=None):
    res = openai.Completion.create(
    prompt = f"{chat_log}{restart_sequence}: {question}{start_sequence}:",
    engine="text-davinci-003",
    temperature=0.2,
    max_tokens=200,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0.3,
    stop=["\n"],
    )
    return str(res['choices'][0]['text'])

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None: 
        chat_log = session_prompt 
    return f"{chat_log}{restart_sequence} {question}{start_sequence}{answer}"

@csrf_exempt
def message(request):
    if request.POST.get("Body"):
        chat_log = request.session.get("chat_log")
        if chat_log is not None:
            if len(chat_log) > 1500 or not chat_log:
                chat_log = session_prompt
        else:
            chat_log = session_prompt
        print(chat_log)
        body = request.POST.get("Body")+"\n"
        answer = ask(body, chat_log)
        request.session["chat_log"] = append_interaction_to_chat_log(body, answer,chat_log)
        msg = MessagingResponse()
        msg.message(answer)
        return HttpResponse(str(msg))
    
    return HttpResponse(str("ok"))