# Copyright (c) 2014, DjaoDjin inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.views.generic import TemplateView
from urldecorators import patterns, include, url

from saas.settings import ACCT_REGEX
from saas.views import OrganizationRedirectView
from saas.views.plans import CartPlanListView
from testsite.views.organization import OrganizationListView
from testsite.views.registration import PersonalRegistrationView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # admin doc and panel
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/register/$',
        PersonalRegistrationView.as_view(
            success_url=reverse_lazy('home')),
        name='registration_register'),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^saas/$',
        OrganizationListView.as_view(), name='saas_organization_list',
        decorators=['django.contrib.auth.decorators.login_required']),
    url(r'^', include('saas.urls.noauth')),
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^billing/cart/',
        login_required(OrganizationRedirectView.as_view(
                pattern_name='saas_organization_cart'),
                       login_url=reverse_lazy('registration_register')),
        name='saas_cart'),
    # saas urls with provider key to implement marketplace.
    url(r'^api/', include('saas.urls.api.cart')),
    url(r'^api/', include('saas.urls.api.provider'),
        decorators=['saas.decorators.requires_direct']),
    url(r'^api/', include('saas.urls.api.subscriber'),
        decorators=['saas.decorators.requires_provider']),
    url(r'^pricing/', CartPlanListView.as_view(), name='saas_cart_plan_list'),
    url(r'^provider/(?P<organization>%s)/' % ACCT_REGEX,
        include('saas.urls.provider'),
        decorators=['saas.decorators.requires_direct']),
    url(r'^billing/(?P<organization>%s)/' % ACCT_REGEX,
        include('saas.urls.billing'),
        decorators=['saas.decorators.requires_direct']),
    url(r'^profile/',
        include('saas.urls.profile'),
        decorators=['saas.decorators.requires_direct']),
    url(r'^users/(?P<user>%s)/' % ACCT_REGEX,
        include('saas.urls.users'),
        decorators=['saas.decorators.requires_direct']),
)
