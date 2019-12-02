"Models for managing oath2 client authorizations."
# -*- coding: utf-8 -*-
import uuid
import datetime
from urllib.parse import urlencode
import requests
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created = models.DateTimeField(_('Created'), auto_now_add=True, editable=False)
    modified = models.DateTimeField(_('Modified'), auto_now=True, editable=False)

    class Meta:
        abstract = True

class Client(TimeStampedModel):
    "Configuration and authentication of an oauth2 clients."
    uid = models.UUIDField(_("UID"), default=uuid.uuid4, unique=True)
    name = models.CharField(_("Name"), max_length=100, unique=True)
    client_id = models.CharField(_("Client id"), max_length=255, unique=True)
    client_secret = models.CharField(_("Client secret"), max_length=255)
    authorization_endpoint = models.URLField(_("Authorization endpoint"), max_length=255)
    token_endpoint = models.URLField(_("Token endpoint"), max_length=255, blank=True, default='')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.PROTECT)
    scope = models.CharField(_("Scope"), max_length=255, blank=True, default='read')

    class Meta:
        verbose_name = _("Oauth2 client")
        verbose_name_plural = _("Oauth2 clients")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        "Saves the client."
        if not self.token_endpoint:
            self.token_endpoint = self.authorization_endpoint
        return super(Client, self).save(*args, **kwargs)

    @property
    def session_state_name(self):
        "Returns the id of the oauth2 authentication process session."
        return str(self.uid)

    @property
    def session_redirect_url_name(self):
        "Returns the name of the redirection view."
        return '{}:redirect-url'.format(str(self.uid))

    def complete_authorization_url(self, request=None):
        "Returns the redirection url."
        info = self._meta.app_label, self._meta.model_name
        view_name = 'admin:%s_%s_complete_authorization' % info
        authorization_url = reverse(view_name, args=(self.uid,))
        return request.build_absolute_uri(authorization_url) if request else authorization_url

    def start_authorization_url(self, request, redirect_url, final_redirection=None):
        """Returns the oauth2 provider url that will be redirected to when starting
        the authorization process.

        Parameters
        ----------
        request
            Django request object
        redirect_url: string
            Redirection url that will be sent to the authorization server.
        final_redirection: string
            If provided, after the redirection from the oauth2 provider, the
            user will be redirected to the url in this parameter.

        Returns
        -------
        url: string
            Returns the url to use to start the authorization process.
        """
        redirect_url = request.build_absolute_uri(redirect_url)
        state = str(uuid.uuid4())
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_url,
            'scope': self.scope,
            'state': state,
        }
        for row in self.params.all():
            params[row.name] = row.value
        encoded_params = urlencode(params)
        result = '{}?{}'.format(self.authorization_endpoint, encoded_params)
        request.session[self.session_state_name] = state
        if final_redirection:
            request.session[self.session_redirect_url_name] = final_redirection
        return result

    def complete_authorization(self, request, redirect_url):
        """Execute this method in the redirection view to fetch the access
        token."""
        state = request.GET['state']
        if request.session[self.session_state_name] != state:
            raise ValueError("Wrong oauth state.")
        del request.session[self.session_state_name]
        code = request.GET['code']
        token_url = '{}?grant_type=authorization_code&client_id={}&client_secret={}&redirect_uri={}&code={}'
        token_url = token_url.format(self.token_endpoint, self.client_id,
            self.client_secret, redirect_url, code)
        response = requests.post(token_url)
        data = response.json()
        access_token = AccessToken()
        access_token.client = self
        access_token.token_type = data['token_type']
        access_token.expires_in = data['expires_in']
        access_token.access_token = data['access_token']
        access_token.refresh_token = data.get('refresh_token', '')
        access_token.scope = data.get('scope', self.scope)
        access_token.save()
        return request.session.pop(self.session_redirect_url_name, None)

class ClientParam(models.Model):
    "Define aditional params to pass the start authorization url."
    client = models.ForeignKey(Client, verbose_name=_("Client"),
        related_name='params', on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=40)
    value = models.TextField(_("Value"), blank=True, default='')

    class Meta:
        verbose_name = _("Client param")
        verbose_name_plural = _("Client params")

    def __str__(self):
        return self.name


class AccessToken(TimeStampedModel):
    """Oauth2 client access token. This object shold be usually generated
    from the oauth2 client authorization process."""
    client = models.ForeignKey(Client, verbose_name=_("Client"), on_delete=models.CASCADE)
    user_id = models.CharField(_("User id"), max_length=255, blank=True, default='')
    username = models.CharField(_("Username"), max_length=255, blank=True, default='')
    token_type = models.CharField(_("Token type"), max_length=255)
    expires_in = models.IntegerField(_("Expires in"))
    access_token = models.CharField(_("Access token"), max_length=255)
    refresh_token = models.CharField(_("Refresh token"), max_length=255)
    scope = models.TextField(_("Scope"), blank=True, default='')

    class Meta:
        verbose_name = _("Access token")
        verbose_name_plural = _("Access tokens")    

    def do_refresh_token(self):
        "Refresh the token"
        url = '{}?grant_type=refresh_token&refresh_token={}&client_id={}&client_secret={}&scope={}'
        url = url.format(self.client.token_endpoint, self.refresh_token, self.client.client_id,
            self.client.client_secret, self.client.scope)
        response = requests.post(url)
        data = response.json()
        self.token_type = data['token_type']
        self.expires_in = data['expires_in']
        self.access_token = data['access_token']
        if 'refresh_token' in data:
            self.refresh_token = data['refresh_token']
        self.save()

    def expiration(self):
        "Returns the expiration date in the local timezone."
        modified = timezone.localtime(self.modified)
        delta = datetime.timedelta(seconds=self.expires_in)
        return modified + delta

    def is_expired(self):
        "Returns if the token is expired."
        return timezone.now() > self.expiration()
