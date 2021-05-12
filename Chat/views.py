from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.urls import reverse
from .models import Chat
from .forms import SignUpForm
import json

@login_required
def home(request):
    user = request.user
    chat_rooms = Chat.objects.filter(members=user)

    context = {
        "chat_rooms": chat_rooms,
        "type": "list"
    }

    return render(request, "chat/group_list.html", context)

@login_required
def room_search(request, search_name):
    chat_search = Chat.objects.filter(room_name__icontains=search_name)

    context = {
        "chat_rooms": chat_search,
        "search_name": search_name,
        "type": "search_list"
    }

    return render(request, "chat/group_list.html", context)

@login_required
def room(request, room_name):
    user = request.user
    chat_model = Chat.objects.filter(room_name=room_name)
    request_room_name = request.POST.get("room_name")
    request_action_name = request.POST.get("action_name")

    if request.method == "POST":
        if user.is_superuser and request_room_name == room_name and \
            request_action_name == "create" and not chat_model.exists():
            chat = Chat.objects.create(room_name=room_name)
            chat.members.add(user)
        elif request_room_name == room_name and request_action_name == "join" \
            and chat_model.exists():
            chat_model[0].members.add(user)
        else:
            return redirect("home")
    else:
        if not chat_model.exists():
            if user.is_superuser:
                return redirect("room_confirm", room_name=room_name, action_name="create")
            else:
                return redirect("home")
        elif chat_model.exists():
            if user not in chat_model[0].members.all():
                return redirect("room_confirm", room_name=room_name, action_name="join")
            else:
                pass

    username = request.user.username

    context = {
        "room_name": room_name,
        "username": mark_safe(json.dumps(username))
    }

    return render(request, "chat/room.html", context)

@login_required
def room_leave(request, room_name):
    user = request.user
    chat = Chat.objects.filter(room_name=room_name)

    if chat.exists():
        if request.method == "POST":
            if user.is_superuser and request.POST.get("room_name") == room_name + "__delete":
                chat[0].delete()
                return redirect("home")

            if user in chat[0].members.all() and request.POST.get("room_name") == room_name:
                chat[0].members.remove(user)
        else:
            if user in chat[0].members.all():
                return redirect("room_confirm", room_name=room_name, action_name="leave")

    return redirect("home")

@login_required
def room_confirm(request, room_name, action_name):
    actions_list = ["join", "create", "leave"]
    if action_name not in actions_list:
        return redirect("home")

    user = request.user
    chat_model = Chat.objects.filter(room_name=room_name)

    context = {
        "chat": (lambda chat: chat_model[0] if chat.exists() else "")(chat_model),
        "room_name": room_name,
        "action_name": action_name,
        "username": request.user.username,
        "url": f"/chat/{room_name}/"
    }

    if chat_model.exists():
        if user in chat_model[0].members.all():
            if action_name == "join":
                return redirect("room", room_name=room_name)
            elif action_name == "leave":
                return render(request, "chat/room_leave_confirm.html", context)
        else:
            if action_name == "join":
                return render(request, "chat/room_confirm.html", context)
            elif action_name == "leave" and user.is_superuser:
                return render(request, "chat/room_leave_confirm.html", context)
    elif not chat_model.exists():
        if user.is_superuser and action_name == "create":
            return render(request, "chat/room_confirm.html", context)
        else:
            pass

    return redirect("home")

def registration(request):
    if request.method == "POST":
        if request.POST.get("submit") == "signup":
            form = SignUpForm(request.POST)
            if form.is_valid():
                form.save()
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'chat/registration.html', {"form": form})
        elif request.POST.get("submit") == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")
            else:
                msg = "نام کاربری و یا رمز عبوری که وارد کردید اشتباه است."
                form = {"errors": {"error": [msg]}}
                return render(request, 'chat/registration.html', {"form": form})

    return render(request, "chat/registration.html")