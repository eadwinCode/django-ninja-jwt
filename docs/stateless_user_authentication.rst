.. _stateless_user_authentication:

Stateless User Authentication
=====================

JWTStatelessUserAuthentication backend
----------------------------------

The ``JWTStatelessUserAuthentication`` backend's ``authenticate`` method does not
perform a database lookup to obtain a user instance.  Instead, it returns a
``ninja_jwt.models.TokenUser`` instance which acts as a
stateless user object backed only by a validated token instead of a record in a
database.  This can facilitate developing single sign-on functionality between
separately hosted Django apps which all share the same token secret key.  To
use this feature, add the
<<<<<<< HEAD:docs/docs/experimental_features.rst
``ninja_jwt.authentication.JWTTokenUserAuthentication`` backend
=======
``rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication`` backend
>>>>>>> cd4ea99424ec7256291253a87f3435fec01ecf0e:docs/stateless_user_authentication.rst
(instead of the default ``JWTAuthentication`` backend) to the Django REST
Framework's ``DEFAULT_AUTHENTICATION_CLASSES`` config setting:

.. code-block:: python

  REST_FRAMEWORK = {
      ...
      'DEFAULT_AUTHENTICATION_CLASSES': (
          ...
<<<<<<< HEAD:docs/docs/experimental_features.rst
          'ninja_jwt.authentication.JWTTokenUserAuthentication',
=======
          'rest_framework_simplejwt.authentication.JWTStatelessUserAuthentication',
>>>>>>> cd4ea99424ec7256291253a87f3435fec01ecf0e:docs/stateless_user_authentication.rst
      )
      ...
  }
  
v5.1.0 has renamed ``JWTTokenUserAuthentication`` to ``JWTStatelessUserAuthentication``, 
but both names are supported for backwards compatibility
