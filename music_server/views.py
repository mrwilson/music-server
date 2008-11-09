from itertools import count, izip

from django.db import connection
from django.contrib.auth import login, authenticate
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden

from music_server.forms import UploadForm, YouTubeForm
from music_server.models import Item, YouTubeQueue

def index(request):
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (reverse('login', request.path)))

        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            q = form.save(commit=False)
            q.user = request.user
            q.ip = request.META.get('REMOTE_ADDR')
            q.save()
            return HttpResponseRedirect(reverse('index'))
    else:
        form = UploadForm()

    return render_to_response('index.html', {
        'queue': izip(count(1), Item.unplayed.all()),
        'upload_form': form,
        'youtube_form': YouTubeForm(),
    }, RequestContext(request))

def youtube(request):
    if request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponseRedirect('%s?next=%s' % (reverse('login', request.path)))

        form = YouTubeForm(request.POST)
        if form.is_valid():
            q = form.save(commit=False)
            q.user = request.user
            q.ip = request.META.get('REMOTE_ADDR')
            q.save()
            return HttpResponseRedirect(reverse('youtube'))
    else:
        form = YouTubeForm()

    return render_to_response('youtube.html', {
        'youtube_form': form,
        'queue': YouTubeQueue.objects.exclude(state='f'),
        'failed': YouTubeQueue.objects.filter(state='f')[:5],
    }, RequestContext(request))

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            d = form.cleaned_data
            user = authenticate(username=d['username'], password=d['password1'])
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = UserCreationForm()

    return render_to_response('registration/register.html', {
        'form': form,
    }, RequestContext(request))

@login_required
def delete(request, item_id):
    get_object_or_404(Item, id=item_id, user=request.user, state='q').delete()
    return HttpResponseRedirect(reverse('index'))

@login_required
def move(request, direction, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user, state='q')
    if direction == 'up':
        item.move_up()
    else:
        item.move_down()
    return HttpResponseRedirect(reverse('index'))
