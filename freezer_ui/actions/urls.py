# (c) Copyright 2014,2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.urls import re_path

from freezer_ui.actions import views

urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),

    re_path(r'^create/(?P<action_id>[^/]+)?$',
            views.ActionWorkflowView.as_view(),
            name='create'),

    re_path(r'^action/(?P<action_id>[^/]+)?$',
            views.ActionView.as_view(),
            name='action'),
]
