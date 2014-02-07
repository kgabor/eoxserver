#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

from itertools import product
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import commit_on_success

from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.resources.coverages import models


class Command(CommandOutputMixIn, BaseCommand):

    args = (
        '-i <eo-object-id-1> [-i <eo-object-id-2> ... ] '
        '-c <collection-id-1> [-c <collection-id-2> ... ]'
    )
    help = "Remove one or more EO-object from one or more collections."

    option_list = BaseCommand.option_list + (
        make_option('-i','--identifier',
            dest='eo_object_ids', action='append', default=None,
            help=("EO-object identifier. Can be present multiple times.") 
        ), 
        make_option('-c','--collection',
            dest='collection_ids', action='append', default=None,
            help=("Collection identifier. Can be present multiple times.") 
        ),
        make_option('-s', '--silent',
            dest="silent", action="store_true", default=False,
            help=("If this option is set, it is no error when an EO-object "
                  "was not included in a collection.")
        )
    )


    @commit_on_success
    def handle(self, eo_object_ids, collection_ids, silent, *args, **kwargs):
        """ 
        """
        if not eo_object_ids:
            raise CommandError("No EO-object ID(s) given.")
        elif not collection_ids:
            raise CommandError("No Collection ID(s) given.")


        for eo_object_id, collection_id in product(eo_object_ids, collection_ids):
            try:
                collection = models.Collection.objects.get(
                    identifier=collection_id
                ).cast()
            except models.Collection.DoesNotExist:
                raise CommandError(
                    "No collection with ID '%s' found." % collection_id
                )

            try:
                eo_object = models.EOObject.objects.get(
                    identifier=eo_object_id
                ).cast()
            except models.Collection.DoesNotExist:
                raise CommandError(
                    "No collection with ID '%s' found." % collection_id
                )
            try:
                collection.remove(eo_object)
            except models.EOObjectToCollectionThrough.DoesNotExist:
                if silent:
                    pass
                else:
                    raise CommandError(
                        "The collection with ID '%s' did not include the "
                        "EO-object with ID '%s'." 
                        % (collection_id, eo_object_id)
                    )
