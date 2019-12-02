=====
Usage
=====

To use Django Oauth Clients 3 in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'oauth_clients3.apps.OauthClients3Config',
        ...
    )

Add Django Oauth Clients 3's URL patterns:

.. code-block:: python

    from oauth_clients3 import urls as oauth_clients3_urls


    urlpatterns = [
        ...
        url(r'^', include(oauth_clients3_urls)),
        ...
    ]
