import urllib

from django.conf import settings
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

class GoogleClient(OAuth2Client):

    def get_redirect_url(self):
        params = {
            'client_id': self.consumer_key,
            'redirect_uri': self.callback_url,
            'scope': self.scope,
            'response_type': 'code'
        }

        try:
          params['hd'] = settings.GOOGLE_DOMAIN
        except:
          pass

        if self.state:
            params['state'] = self.state
        return '%s?%s' % (self.authorization_url, urllib.urlencode(params))
