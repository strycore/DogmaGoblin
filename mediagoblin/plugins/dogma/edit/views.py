# -*- coding: utf-8 -*-
# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

_log = logging.getLogger(__name__)

from datetime import datetime

from werkzeug.exceptions import Forbidden
from werkzeug.utils import secure_filename

from mediagoblin import messages
from mediagoblin import mg_globals

from mediagoblin.auth import lib as auth_lib
from mediagoblin.edit import forms
from mediagoblin.edit.lib import may_edit_media
from mediagoblin.decorators import (require_active_login, active_user_from_url,
     get_media_entry_by_id,
     user_may_alter_collection, get_user_collection)
from mediagoblin.tools.response import render_to_response, \
    redirect, redirect_obj
from mediagoblin.tools.translate import pass_to_ugettext as _
from mediagoblin.tools.text import (
    convert_to_tag_list_of_dicts, media_tags_as_string)
from mediagoblin.tools.url import slugify
from mediagoblin.db.util import check_media_slug_used, check_collection_slug_used

import mimetypes

@get_media_entry_by_id
@require_active_login
def edit_track(request, media):
    if not may_edit_media(request, media):
        raise Forbidden("User may not edit this media")

    defaults = dict(
        title=media.title,
        slug=media.slug,
        description=media.description,
        tags=media_tags_as_string(media.tags),
        license=media.license)
    _log.info(media.get_author)

    form = forms.EditForm(
        request.form,
        **defaults)

    if request.method == 'POST' and form.validate():
        # Make sure there isn't already a MediaEntry with such a slug
        # and userid.
        slug = slugify(form.slug.data)
        slug_used = check_media_slug_used(media.uploader, slug, media.id)

        if slug_used:
            form.slug.errors.append(
                _(u'An entry with that slug already exists for this user.'))
        else:
            media.title = form.title.data
            media.description = form.description.data
            media.tags = convert_to_tag_list_of_dicts(
                                   form.tags.data)

            media.license = unicode(form.license.data) or None
            media.slug = slug
            media.save()

            return redirect_obj(request, media)

    if request.user.is_admin \
            and media.uploader != request.user.id \
            and request.method != 'POST':
        messages.add_message(
            request, messages.WARNING,
            _("You are editing another user's media. Proceed with caution."))

    return render_to_response(
        request,
        'dogma/edit/edit.html',
        {'media': media,
         'form': form})
