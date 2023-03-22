# -*- coding: utf-8 -*-
"""

    mslib.mscolab.forms.py
    ~~~~~~~~~~~~~~~~~~~~~~

    Forms for mscolab server

    This file is part of MSS.

    :copyright: Copyright 2023 Nilupul Manodya
    :copyright: Copyright 2023 by the MSS team, see AUTHORS.
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


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email


class ResetRequestForm(FlaskForm):
    """Form for requesting a password reset"""
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    submit = SubmitField(label='Reset password', validators=[DataRequired()])


class ResetPasswordForm(FlaskForm):
    """Form for setting a new password"""
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('password',
                                                         message='Passwords must match')])
    submit = SubmitField(label='Change Password', validators=[DataRequired()])
