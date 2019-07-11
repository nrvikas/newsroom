from flask import render_template, url_for
from flask_babel import gettext

from newsroom.email import send_email
from newsroom.utils import get_agenda_dates, get_location_string, get_links, get_public_contacts
from newsroom.template_filters import is_admin_or_internal
from newsroom.settings import get_settings_collection, GENERAL_SETTINGS_LOOKUP


def send_coverage_notification_email(user, agenda, wire_item):
    if user.get('receive_email'):
        kwargs = dict(
            agenda=agenda,
            item=wire_item,
            section='agenda',
        )
        send_email(
            to=[user['email']],
            subject=gettext('New coverage'),
            text_body=render_template('agenda_new_coverage_email.txt', **kwargs),
            html_body=render_template('agenda_new_coverage_email.html', **kwargs)
        )


def send_agenda_notification_email(user, agenda, message, subject, original_agenda, coverage_updates,
                                   related_planning_removed, coverage_updated):
    if agenda and user.get('receive_email'):
        kwargs = dict(
            message=message,
            agenda=agenda,
            dateString=get_agenda_dates(agenda if agenda.get('dates') else original_agenda, date_paranthesis=True),
            location=get_location_string(agenda),
            contacts=get_public_contacts(agenda),
            links=get_links(agenda),
            is_admin=is_admin_or_internal(user),
            original_agenda=original_agenda,
            coverage_updates=coverage_updates,
            related_planning_removed=related_planning_removed,
            coverage_updated=coverage_updated,
        )
        send_email(
            to=[user['email']],
            subject=subject,
            text_body=render_template('agenda_updated_email.txt', **kwargs),
            # html_body=render_template('agenda_updated_email.html', **kwargs)
        )


def send_coverage_request_email(user, message, item):
    """
    Forms and sends coverage request email
    :param user: User that makes the request
    :param message: Request message
    :param item: agenda item that request is made against
    :return:
    """

    general_settings = get_settings_collection().find_one(GENERAL_SETTINGS_LOOKUP)
    if not general_settings:
        return

    recipients = general_settings.get('values').get('coverage_request_recipients').split(',')
    assert recipients
    assert isinstance(recipients, list)
    url = url_for('agenda.item', _id=item, _external=True, featured='false')
    name = '{} {}'.format(user.get('first_name'), user.get('last_name'))
    email = user.get('email')

    subject = gettext('A new coverage request')
    text_body = render_template('coverage_request_email.txt', name=name, email=email,
                                message=message, url=url)
    html_body = render_template('coverage_request_email.html', name=name, email=email,
                                message=message, url=url)

    send_email(to=recipients, subject=subject, text_body=text_body, html_body=html_body)
