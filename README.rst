=============================
Django Oauth Clients 3
=============================

.. image:: https://badge.fury.io/py/dj-oauth-clients3.svg
    :target: https://badge.fury.io/py/dj-oauth-clients3

.. image:: https://travis-ci.org/kverdecia/dj-oauth-clients3.svg?branch=master
    :target: https://travis-ci.org/kverdecia/dj-oauth-clients3

.. image:: https://codecov.io/gh/kverdecia/dj-oauth-clients3/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/kverdecia/dj-oauth-clients3

Django app for handling oauth2 clients (without support for python2 and django1.x)

Documentation
-------------

The full documentation is at https://dj-oauth-clients3.readthedocs.io.

Quickstart
----------

Install Django Oauth Clients 3::

    pip install dj-oauth-clients3

Add it to your `INSTALLED_APPS`:

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

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
