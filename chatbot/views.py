from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat
from django.utils import timezone
import boto3
import json

def ask_openai(message):
    # promt =f"""{message}"""
    bedrock = boto3.client(service_name="bedrock-runtime")
    payload = {
        "prompt":message,
        "max_gen_len": 512,
        "temperature": 0.5,
        "top_p": 0.9
    }
    body = json.dumps(payload)
    modelId='meta.llama3-70b-instruct-v1:0'
    response=bedrock.invoke_model(
        body=body,
        modelId=modelId,
        accept='application/json',
        contentType= "application/json"
    )

    response_body = json.loads(response.get("body").read())

    response_text = response_body['generation']
    # print(response_text)
    return response_text

# Create your views here.
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)
    if request.method == "POST":
        message = request.POST.get('message')
        response = ask_openai(message)

        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats':chats})


def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username = username, password = password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_messages = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_messages})
    else:
        return render(request, 'login.html')
    
    
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username,email,password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = "Error creating account"
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = "password not matched"
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect(login)
