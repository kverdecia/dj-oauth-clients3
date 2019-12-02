"Admin interface for defining and authorizing oauth2 clients."
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.formats import localize
from django.conf.urls import url
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from . import models


class TokenInline(admin.TabularInline):
    "Inline admin interface for oauth2 client's access tokens"
    fields = ('user_id', 'username', 'token_type', 'expires_in', 'access_token', 'refresh_token')
    readonly_fields = fields
    extra = 0
    model = models.AccessToken

class ParamInline(admin.TabularInline):
    "Inline admin interface for oauth2 client's extra parameters."
    fields = ('name', 'value')
    extra = 2
    model = models.ClientParam

class ClientAdmin(admin.ModelAdmin):
    "Admin interface for managing oauth2 clients."
    list_display = ('uid', 'name', 'client_id', 'authorization_endpoint', 'token_endpoint',
        'scope', 'creator', 'created', 'modified')
    fields = ('uid', 'name', 'client_id', 'client_secret', 'authorization_endpoint',
        'token_endpoint', 'creator', 'scope', 'created', 'modified', 'complete_authorization_url')
    readonly_fields = ('uid', 'creator', 'created', 'modified', 'complete_authorization_url')
    inlines = [ParamInline, TokenInline]

    def get_urls(self):
        urls = super(ClientAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        my_urls = [
            url(r'^(.+)/complete-authorization/$', self.complete_authorization, name='%s_%s_complete_authorization' % info),
        ]
        return my_urls + urls

    def complete_authorization(self, request, uid):
        "View to complete oauth2 authorization"
        client = get_object_or_404(models.Client, uid=uid)
        redirect_url = client.complete_authorization_url(request)
        final_redirection = client.complete_authorization(request, redirect_url)
        msg = ugettext("Oauth client authorized.")
        self.message_user(request, msg, messages.INFO)
        if final_redirection:
            return redirect(final_redirection)
        url_name = 'admin:{}_{}_change'.format(self.model._meta.app_label, self.model._meta.model_name)
        return redirect(url_name, client.pk)

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.creator = request.user
        super(ClientAdmin, self).save_model(request, obj, form, change)

    def response_change(self, request, obj):
        if '_authorize-client' in request.POST:
            redirect_url = obj.complete_authorization_url(request)
            authorization_url = obj.start_authorization_url(request, redirect_url)
            return redirect(authorization_url)
        return super(ClientAdmin, self).response_change(request, obj)


class TokenAdmin(admin.ModelAdmin):
    "Admin interface for managing oauth2 client access tokens."
    list_display = ('client', 'user_id', 'username', 'token_type', 'get_expiration',
        'get_expired', 'modified')
    fields = ('client', 'user_id', 'username', 'token_type', 'scope', 'expires_in',
        'get_expiration', 'get_expired', 'access_token', 'refresh_token', 'created',
        'modified')
    readonly_fields = fields
    list_filter = ('client', 'created', 'modified')
    actions = ['refresh_tokens']

    def has_add_permission(self, request):
        return False

    def refresh_tokens(self, request, queryset):
        "Action for refreshing tokens."
        for access_token in queryset:
            access_token.do_refresh_token()
        msg = ugettext("Selected tokens refreshed.")
        self.message_user(request, msg, messages.INFO)
    refresh_tokens.short_description = _("Refresh selected tokens")

    def get_expiration(self, obj):
        "Column for showing the expiration date."
        return localize(obj.expiration())
    get_expiration.short_description = _("Expiration")

    def get_expired(self, obj):
        "Column for showing if the toke is expired."
        return obj.is_expired()
    get_expired.short_description = _("Expired")
    get_expired.boolean = True


admin.site.register(models.Client, ClientAdmin)
admin.site.register(models.AccessToken, TokenAdmin)
