Getting Started
===============

.. note:: While bobsled has been in use for quite a while by the project, the effort to document it and make it easier for others to use has just begun.  Please bear with us, and if you get stuck or notice anything weird please file an issue: https://github.com/stateautomata/bobsled/issues


Running with Docker Compose
---------------------------

Bobsled is designed to be run as a Docker image.  While a future version of this documentation will tackle the issue of deployment, we'll get started with docker-compose.  If you don't have Docker Compose installed, `you can install Docker on your local system <https://docs.docker.com/get-docker/>`_ and you should be able to follow along just fine.


Environment Configuration
-------------------------

Bobsled's core configuration is done via environment variables.


At a minimum you'll need to set:

``BOBSLED_SECRET_KEY`` 
  Set to a random string that is not publicly known, used for token signing.


There are two types of configuration required forSystem-wide configuration is done via environment variables.
