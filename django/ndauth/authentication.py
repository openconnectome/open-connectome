# myapp/authentication.py
from django.contrib.auth.models import User
from django.utils.six import text_type
from rest_framework import authentication
from rest_framework import exceptions
from nduser.models import Token
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token as AuthToken
from django.http import HttpResponseForbidden

from webservices.ndwserror import NDWSError
import logging
logger=logging.getLogger("neurodata")

def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.
    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if isinstance(auth, text_type):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth

class AnonAllowedAuthentication(authentication.TokenAuthentication):
    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            #If this is the case someone passed an empty user_token which should be treated as valid but anonymous
            return None

        elif len(auth) > 2:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        key = token
        model = AuthToken
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            return None

        return (token.user, token)



class PublicAuthentication(authentication.BaseAuthentication):
  
  def has_permission(self, request, view):
    web_path = request.path
    if not web_path: # Some very odd scenario
      raise IOError('Could not get web_path from request')
    
    try:
      argus = web_path.split('/')
      # Expects args in order: ''|nd|ocp , ''|nd|ocp , App , View , Token , Arguements
      if argus[0] in ['','nd','ocp']:
        argus = argus[1:]
      if argus[0] in ['','nd','ocp']:
        argus = argus[1:]
      if argus[0] in ['','nd','ocp']:
        argus = argus[1:]
      
      # checking for mcfc in catmaid calls
      if argus[0] == 'catmaid':
        exp_token = argus[2]
      else:
        exp_token = argus[1]

      pp_tokens = Token.objects.filter(public=1)
      pub_tokens = []
      for v in pp_tokens.values():
        pub_tokens.append(v['token_name'])

      if (exp_token in pub_tokens):
        return True

      try:
        if not request.user.is_superuser:
          m_tokens = Token.objects.filter(user=request.user.id)
          tokens = []
          for v in m_tokens.values():
            tokens.append(v['token_name'])
          if not exp_token in tokens:
            raise NDWSError ("Token {} does not exist or you do not have sufficient permissions to access it. {}".format(exp_token, pub_tokens))
          else:
            return True
        else:
          return True
      except Exception as e:
        logger.warning("Error in authenticating user in NDAUTH: {}".format(e))
        return False

    except Exception as e:
      raise e
