# -*- coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig


class OauthClients3Config(AppConfig):
    name = 'oauth_clients3'
    verbose_name = _("Oauth client")
    verbose_name_plural = _("Oauth clients")
