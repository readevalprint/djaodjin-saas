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

"""Manage Profile information"""

import logging

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.generic import ListView, TemplateView, UpdateView
from django.utils.decorators import method_decorator

from saas.forms import OrganizationForm, ManagerAndOrganizationForm
from saas.mixins import OrganizationMixin, ProviderMixin
from saas.models import Organization, Subscription

LOGGER = logging.getLogger(__name__)


class ContributorListBaseView(ListView):
    """
    List of contributors for an organization.

    Must be used with an OrganizationMixin or a ProviderMixin.
    """

    paginate_by = 10
    template_name = 'saas/contributor_list.html'

    # Make pylint happy: ``get_organization`` will be picked up correctly
    # in the derived classes.
    def get_organization(self):
        return self

    def get_queryset(self):# XXX not necessary since we use a REST API,
                           # yet need to find out to get the pagination correct.
        self.organization = self.get_organization()
        return self.organization.contributors.all()


class ProviderContributorListView(ProviderMixin, ContributorListBaseView):
    """
    List of contributors for the site provider.
    """
    pass


class ContributorListView(OrganizationMixin, ContributorListBaseView):
    """
    List of contributors for an organization.
    """
    pass


class ManagerListBaseView(ListView):
    """
    List of managers for an organization.

    Must be used with an OrganizationMixin or a ProviderMixin.
    """

    paginate_by = 10
    template_name = 'saas/manager_list.html'

    # Make pylint happy: ``get_organization`` will be picked up correctly
    # in the derived classes.
    def get_organization(self):
        return self

    def get_queryset(self):# XXX not necessary since we use a REST API,
                           # yet need to find out to get the pagination correct.
        self.organization = self.get_organization()
        return self.organization.managers.all()


class ProviderManagerListView(ProviderMixin, ManagerListBaseView):
    """
    List of managers for the site provider.
    """
    pass


class ManagerListView(OrganizationMixin, ManagerListBaseView):
    """
    List of managers for an organization.
    """
    pass


class SubscriberListView(ProviderMixin, TemplateView):
    """
    List of organizations subscribed to a plan provided by the organization.
    """

    template_name = 'saas/subscriber_list.html'


class SubscriptionListView(OrganizationMixin, ListView):
    """
    List of Plans this organization is subscribed to.
    """

    model = Subscription
    paginate_by = 10
    template_name = 'saas/subscription_list.html'

    def get_queryset(self):
        self.organization = self.get_organization()
        return Subscription.objects.active_for(self.organization)

    def get_context_data(self, **kwargs):
        context = super(SubscriptionListView, self).get_context_data(**kwargs)
        context.update({'subscriptions': context['object_list']})
        return context


class OrganizationProfileView(OrganizationMixin, UpdateView):

    model = Organization
    slug_field = 'slug'
    slug_url_kwarg = 'organization'
    template_name = "saas/organization_profile.html"

    @method_decorator(transaction.atomic)
    def form_valid(self, form):
        if 'is_bulk_buyer' in form.cleaned_data:
            self.object.is_bulk_buyer = form.cleaned_data['is_bulk_buyer']
        else:
            self.object.is_bulk_buyer = False
        manager = self.attached_manager(self.object)
        if manager:
            if form.cleaned_data.get('slug', None):
                manager.username = form.cleaned_data['slug']
            if form.cleaned_data['full_name']:
                name_parts = form.cleaned_data['full_name'].split(' ')
                if len(name_parts) > 1:
                    manager.first_name = name_parts[0]
                    manager.last_name = ' '.join(name_parts[1:])
                else:
                    manager.first_name = form.cleaned_data['full_name']
                    manager.last_name = ''
            if form.cleaned_data['email']:
                manager.email = form.cleaned_data['email']
            manager.save()
        return super(OrganizationProfileView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(
            OrganizationProfileView, self).get_context_data(**kwargs)
        context.update({"attached_manager": self.attached_manager(self.object)})
        return context

    def get_form_class(self):
        if self.attached_manager(self.object):
            # There is only one manager so we will add the User fields
            # to the form so they can be updated at the same time.
            return ManagerAndOrganizationForm
        return OrganizationForm

    def get_initial(self):
        kwargs = super(OrganizationProfileView, self).get_initial()
        queryset = Organization.objects.providers_to(
            self.object).filter(managers__id=self.request.user.id)
        if queryset.exists():
            kwargs.update({'is_bulk_buyer': self.object.is_bulk_buyer})
        return kwargs

    def get_success_url(self):
        messages.info(self.request, 'Profile Updated.')
        return reverse('saas_organization_profile', args=(self.object,))


class ProviderProfileView(ProviderMixin, OrganizationProfileView):

    def get_object(self, queryset=None):
        return self.get_organization()

    def get_success_url(self):
        messages.info(self.request, 'Profile Updated.')
        return reverse('saas_provider_profile',)
