import oauth, time, datetime

try:
    import simplejson
except ImportError:
    try:
        import json as simplejson
    except ImportError:
        try:
            from django.utils import simplejson
        except:
            raise "Requires either simplejson, Python 2.6 or django.utils!"

from django.http import *
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from twitter_app.utils import *

CONSUMER = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)


def main(request):
    if request.session.has_key('access_token'):
        return HttpResponseRedirect(reverse('twitter_oauth_friend_list'))
    else:
        return render_to_response('twitter_app/base.html')

def unauth(request):
    response = HttpResponseRedirect(reverse('twitter_oauth_main'))
    request.session.clear()
    return response

def auth(request, success_view, failure_view):
    "/auth/"
    try:
        token = get_unauthorised_request_token(CONSUMER)
        auth_url = get_authorisation_url(CONSUMER, token)
        request.session['unauthed_token'] = token.to_string()   

        return HttpResponseRedirect(auth_url)

    except:
        return HttpResponseRedirect(reverse(failure_view) + '?error=httpauth')

def return_(request, success_view, failure_view):
    "/return/"
    unauthed_token = request.session.get('unauthed_token', None)
    if not unauthed_token:
        return HttpResponseRedirect(reverse(failure_view) + '?error=session')

    token = oauth.OAuthToken.from_string(unauthed_token)   
    if token.key != request.GET.get('oauth_token', 'no-token'):
        return HttpResponseRedirect(reverse(failure_view) + '?error=match')

    try:
        access_token = exchange_request_token_for_access_token(CONSUMER, token)
        request.session['access_token'] = access_token.to_string()

        # Check if the token works on Twitter
        auth = is_authenticated(CONSUMER, access_token)
        if auth:
            # Load the credidentials from Twitter into JSON
            creds = simplejson.loads(auth)

            request.session['twitter_name'] = creds['screen_name']
            return HttpResponseRedirect(reverse(success_view))
    except:
        pass

    return HttpResponseRedirect(reverse(failure_view) + '?error=return')

def friend_list(request):
    users = []
    
    access_token = request.session.get('access_token', None)
    if not access_token:
        return HttpResponse("You need an access token!")
    token = oauth.OAuthToken.from_string(access_token)   
    
    # Check if the token works on Twitter
    auth = is_authenticated(CONSUMER, token)
    if auth:
        # Load the credidentials from Twitter into JSON
        creds = simplejson.loads(auth)
        name = creds.get('name', creds['screen_name']) # Get the name
        
        # Get number of friends. The API only returns 100 results per page,
        # so we might need to divide the queries up.
        friends_count = str(creds.get('friends_count', '100'))
        pages = int( (int(friends_count)/100) ) + 1
        pages = min(pages, 10) # We only want to make ten queries
        
        
        
        for page in range(pages):
            friends = get_friends(CONSUMER, token, page+1)
            
            # if the result is '[]', we've reached the end of the users friends
            if friends == '[]': break
            
            # Load into JSON
            json = simplejson.loads(friends)

            users.append(json)
    
    return render_to_response('twitter_app/list.html', {'users': users})
