# -*- coding: utf-8 -*-
"""

    mslib.mscolab.mail
    ~~~~~~~~~~~~~~~~~~

    sends the mails of the mscolab server, e.g. for the confirmation of an email address

    This file is part of MSS.

    :copyright: Copyright 2021 Reimar Bauer
    :copyright: Copyright 2021-2026 by the MSS team, see AUTHORS.
    :license: APACHE-2.0, see LICENSE for details.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging

from flask import current_app
from flask_mail import Message


def send_email(to, subject, template):
    if current_app.config['MAIL_DEFAULT_SENDER'] is not None:
        msg = Message(
            subject,
            recipients=[to],
            html=template,
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        try:
            current_app.mail.send(msg)
        except (IOError, AttributeError):
            logging.error("Can't send email to %s", to)
    else:
        logging.debug("setup user verification by email")
