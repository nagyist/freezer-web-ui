# Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import logging

import datetime
import re

from functools import wraps

from django.urls import reverse
from django.template.defaultfilters import date as django_date
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import get_user_home
from oslo_utils import uuidutils


LOG = logging.getLogger(__name__)


def create_dict(**kwargs):
    """Create a dict only with values that exists so we avoid send keys with

    None values
    """
    return {k: v for k, v in kwargs.items() if v}


def timestamp_to_string(ts):
    return django_date(
        datetime.datetime.fromtimestamp(int(ts)),
        'SHORT_DATETIME_FORMAT')


def create_dummy_id():
    """Generate a dummy id for documents generated by the scheduler.

    This is needed when the scheduler creates jobs with actions attached
    directly, those actions are not registered in the db.
    """
    return uuidutils.generate_uuid(dashed=False)


def get_action_ids(ids):
    """Return an ordered list of actions for a new job

    """
    ids = ids.split('===')
    return [i for i in ids if i]


def assign_and_remove(source_dict, dest_dict, key):
    """Assign a value to a destination dict from a source dict

    if the key exists
    """
    if key in source_dict:
        dest_dict[key] = source_dict.pop(key)


class SessionObject(object):
    def __init__(self, session_id, description, status, jobs,
                 start_datetime, interval, end_datetime):
        self.session_id = session_id
        self.id = session_id
        self.description = description
        self.status = status
        self.jobs = jobs or []
        self.schedule_start_date = start_datetime
        self.schedule_end_date = end_datetime
        self.schedule_interval = interval


class JobObject(object):
    def __init__(self, job_id, description, result, event, client_id='_'):
        self.job_id = job_id
        self.id = job_id
        self.description = description
        self._result = result
        self._event = event
        # Checking if client_id composed like <tenant_id>_<hostname>
        if re.search("^[a-z0-9]{32}_.+", client_id):
            self.client_id = client_id.split('_')[1]
        else:
            self.client_id = client_id

    @property
    def event(self):
        return self._event or 'stop'

    @property
    def result(self):
        return self._result or 'pending'


class JobsInSessionObject(object):
    def __init__(self, job_id, session_id, client_id, result):
        self.job_id = job_id
        self.session_id = session_id
        self.id = session_id
        self.client_id = client_id
        self.result = result or 'pending'


class ActionObject(object):
    def __init__(self, action_id=None, action=None, backup_name=None,
                 job_id=None):

        # action basic info
        self.id = action_id
        self.action_id = action_id or create_dummy_id()
        self.action = action or 'backup'
        self.backup_name = backup_name or 'no backup name available'
        self.job_id = job_id


class ActionObjectDetail(object):
    def __init__(self, action_id=None, action=None, backup_name=None,
                 path_to_backup=None, storage=None, mode=None, container=None,
                 mandatory=None, max_retries=None, max_retries_interval=None):

        # action basic info
        self.id = action_id
        self.action_id = action_id or create_dummy_id()
        self.action = action or 'backup'
        self.backup_name = backup_name or 'no backup name available'
        self.path_to_backup = path_to_backup
        self.storage = storage or 'swift'
        self.mode = mode or 'fs'
        self.container = container

        # action rules
        self.mandatory = mandatory
        self.max_retries = max_retries
        self.max_retries_interval = max_retries_interval


class BackupObject(object):
    def __init__(self, backup_id=None, action=None, time_stamp=None,
                 backup_name=None, backup_media=None, path_to_backup=None,
                 hostname=None, level=None, container=None,
                 curr_backup_level=None, encrypted=None,
                 total_broken_links=None, excluded_files=None, storage=None,
                 ssh_host=None, ssh_key=None, ssh_username=None,
                 ssh_port=None, mode=None):
        self.backup_id = backup_id
        self.id = backup_id
        self.backup_name = backup_name
        self.action = action or 'backup'
        self.time_stamp = time_stamp
        self.backup_media = backup_media or 'fs'
        self.path_to_backup = path_to_backup
        self.hostname = hostname
        self.container = container
        self.level = level
        self.curr_backup_level = curr_backup_level or 0
        self.encrypted = encrypted
        self.total_broken_links = total_broken_links or 0
        self.excluded_files = excluded_files
        self.storage = storage
        self.ssh_host = ssh_host
        self.ssh_key = ssh_key
        self.ssh_username = ssh_username
        self.ssh_port = ssh_port or 22
        self.mode = mode or 'fs'


class ClientObject(object):
    def __init__(self, hostname, client_id, client_uuid):
        self.hostname = hostname
        self.client_id = client_id
        self.uuid = client_uuid
        self.id = client_id


def shield(message, redirect=''):
    """decorator to reduce boilerplate try except blocks for horizon functions

    :param message: a str error message
    :param redirect: a str with the redirect namespace without including
                     horizon:disaster_recovery:
                     eg. @shield('error', redirect='jobs:index')
    """
    def wrap(function):

        @wraps(function)
        def wrapped_function(view, *args, **kwargs):

            try:
                return function(view, *args, **kwargs)
            except Exception as error:
                LOG.exception(error)
                namespace = "horizon:disaster_recovery:"
                r = reverse("{0}{1}".format(namespace, redirect))

                if view.request.path == r:
                    # To avoid an endless loop, we must not redirect to the
                    # same page on which the error happened
                    user_home = get_user_home(view.request.user)
                    exceptions.handle(view.request, _(str(error)),
                                      redirect=user_home)
                else:
                    exceptions.handle(view.request, _(str(error)),
                                      redirect=r)

        return wrapped_function
    return wrap


def timestamp_to_iso(ts):
    """Generate an iso date from time stamp

    :param ts: time stamp
    :return: iso date
    """
    return datetime.datetime.fromtimestamp(ts).isoformat()
