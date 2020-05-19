Bobsled
=======

Source:
  https://github.com/stateautomata/bobsled/
Issue Tracker:
  https://github.com/stateautomata/bobsled/issues/

.. image:: https://travis-ci.com/stateautomata/bobsled.svg?branch=master
    :target: https://travis-ci.com/stateautomata/bobsled

What is Bobsled?
----------------

Bobsled is a tool to manage & run all of your recurring jobs in one place.  It exists somewhere between cron and CI tools, and provides the ability to run recurring or one-off tasks with minimal overhead while providing features like easy configuration management and monitoring via a web interface.

The project grew out of `Open States <https://openstates.org>`_.  Open States runs hundreds of nightly scrapers to aggregate information on state legislatures, and we needed to know which of our jobs were failing at any given point, run one-offs, keep logs for review, etc.   While we'd relied on tools like Jenkins and cron jobs in the past, bobsled is the product of years of refinement to our process.

If you're curious to see a production instance, you can see Open States' bobsled instance at https://bobsled.openstates.org/

If you or your organization face similar challenges, bobsled might be a good fit for you.

Features
--------

* Tasks scheduled with crontab-like syntax.
* Web interface to view status of running and finished tasks.
* Task & Environment configuration is done via YAML, with support for reading YAML from a GitHub repository.
* Configurable environments that allow bundles of related environment variables to be shared between tasks.
* Pluggable backends: run tasks on local Docker daemon, or remotely via Amazon ECS.
* Aggregated logs, with secrets masked by default.
* Ability to trigger one-off runs of jobs from web interface.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   configuration
