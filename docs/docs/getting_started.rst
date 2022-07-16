.. _getting_started:

Getting started
===============

Requirements
------------

* Python (3.7, 3.8, 3.9, 3.10)
* Django (2.2, 3.1, 3.2, 4.0)
* Django REST Framework (3.10, 3.11, 3.12, 3.13)

These are the officially supported python and package versions.  Other versions
will probably work.  You're free to modify the tox config and see what is
possible.

Installation
------------

<<<<<<< HEAD:docs/docs/getting_started.rst
Ninja JWT can be installed with pip::
=======
Simple JWT can be installed with pip:

.. code-block:: console
>>>>>>> cd4ea99424ec7256291253a87f3435fec01ecf0e:docs/getting_started.rst

  pip install djangorestframework-simplejwt


Cryptographic Dependencies (Optional)
-------------------------------------

If you are planning on encoding or decoding tokens using certain digital
signature algorithms (i.e. RSA and ECDSA; visit PyJWT for other algorithms), you will need to install the
cryptography_ library. This can be installed explicitly, or as a required
extra in the ``djangorestframework-simplejwt`` requirement:

.. code-block:: console

  pip install djangorestframework-simplejwt[crypto]

The ``djangorestframework-simplejwt[crypto]`` format is recommended in requirements
files in projects using ``Simple JWT``, as a separate ``cryptography`` requirement
line may later be mistaken for an unused requirement and removed.

.. _`cryptography`: https://cryptography.io

Project Configuration
---------------------

Then, your django project must be configured to use the library.  In
``settings.py``, add
``ninja_jwt.authentication.JWTAuthentication`` to the list of
authentication classes:

.. code-block:: python

  REST_FRAMEWORK = {
      ...
      'DEFAULT_AUTHENTICATION_CLASSES': (
          ...
          'ninja_jwt.authentication.JWTAuthentication',
      )
      ...
  }

Also, in your root ``urls.py`` file (or any other url config), include routes
for Ninja JWT's ``TokenObtainPairView`` and ``TokenRefreshView`` views:

.. code-block:: python

  from ninja_jwt.views import (
      TokenObtainPairView,
      TokenRefreshView,
  )

  urlpatterns = [
      ...
      path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
      path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
      ...
  ]

You can also include a route for Ninja JWT's ``TokenVerifyView`` if you wish to
allow API users to verify HMAC-signed tokens without having access to your
signing key:

.. code-block:: python
<<<<<<< HEAD:docs/docs/getting_started.rst
  
  from ninja_jwt.views import TokenVerifyView
  
=======

  from rest_framework_simplejwt.views import TokenVerifyView

>>>>>>> cd4ea99424ec7256291253a87f3435fec01ecf0e:docs/getting_started.rst
  urlpatterns = [
      ...
      path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
      ...
  ]

<<<<<<< HEAD:docs/docs/getting_started.rst
If you wish to use localizations/translations, simply add 
``ninja_jwt`` to ``INSTALLED_APPS``.
=======
If you wish to use localizations/translations, simply add
``rest_framework_simplejwt`` to ``INSTALLED_APPS``.
>>>>>>> cd4ea99424ec7256291253a87f3435fec01ecf0e:docs/getting_started.rst

.. code-block:: python

  INSTALLED_APPS = [
      ...
      'ninja_jwt',
      ...
  ]


Usage
-----

To verify that Ninja JWT is working, you can use curl to issue a couple of
test requests:

.. code-block:: bash

  curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"username": "davidattenborough", "password": "boatymcboatface"}' \
    http://localhost:8000/api/token/

  ...
  {
    "access":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoxLCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiY29sZF9zdHVmZiI6IuKYgyIsImV4cCI6MTIzNDU2LCJqdGkiOiJmZDJmOWQ1ZTFhN2M0MmU4OTQ5MzVlMzYyYmNhOGJjYSJ9.NHlztMGER7UADHZJlxNG0WSi22a2KaYSfd1S-AuT7lU",
    "refresh":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoxLCJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImNvbGRfc3R1ZmYiOiLimIMiLCJleHAiOjIzNDU2NywianRpIjoiZGUxMmY0ZTY3MDY4NDI3ODg5ZjE1YWMyNzcwZGEwNTEifQ.aEoAYkSJjoWH1boshQAaTkf8G3yn0kapko6HFRt7Rh4"
  }

You can use the returned access token to prove authentication for a protected
view:

.. code-block:: bash

  curl \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoxLCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiY29sZF9zdHVmZiI6IuKYgyIsImV4cCI6MTIzNDU2LCJqdGkiOiJmZDJmOWQ1ZTFhN2M0MmU4OTQ5MzVlMzYyYmNhOGJjYSJ9.NHlztMGER7UADHZJlxNG0WSi22a2KaYSfd1S-AuT7lU" \
    http://localhost:8000/api/some-protected-view/

When this short-lived access token expires, you can use the longer-lived
refresh token to obtain another access token:

.. code-block:: bash

  curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"refresh":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoxLCJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImNvbGRfc3R1ZmYiOiLimIMiLCJleHAiOjIzNDU2NywianRpIjoiZGUxMmY0ZTY3MDY4NDI3ODg5ZjE1YWMyNzcwZGEwNTEifQ.aEoAYkSJjoWH1boshQAaTkf8G3yn0kapko6HFRt7Rh4"}' \
    http://localhost:8000/api/token/refresh/

  ...
  {"access":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoxLCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiY29sZF9zdHVmZiI6IuKYgyIsImV4cCI6MTIzNTY3LCJqdGkiOiJjNzE4ZTVkNjgzZWQ0NTQyYTU0NWJkM2VmMGI0ZGQ0ZSJ9.ekxRxgb9OKmHkfy-zs1Ro_xs1eMLXiR17dIDBVxeT-w"}
