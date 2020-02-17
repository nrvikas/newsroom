from flask import json
from pytest import fixture
from bson import ObjectId
from .test_users import test_login_succeeds_for_admin, init as user_init  # noqa
from .fixtures import PUBLIC_USER_ID
from newsroom.monitoring.email_alerts import MonitoringEmailAlerts
from unittest import mock
from .utils import mock_send_email
from superdesk.utc import utcnow, utc_to_local
from datetime import timedelta
from superdesk import get_resource_service


company_id = "5c3eb6975f627db90c84093c"


@fixture(autouse=True)
def init(app):
    app.data.insert('companies', [{
        '_id': ObjectId(company_id),
        'phone': '2132132134',
        'sd_subscriber_id': '12345',
        'name': 'Press Co.',
        'is_enabled': True,
        'contact_name': 'Tom'
    }])

    app.data.insert('users', [{
        '_id': ObjectId("5c53afa45f627d8333220f15"),
        'email': 'foo_user@bar.com',
        'first_name': 'Foo_First_name',
        'is_enabled': True,
        'receive_email': True,
        'company': '',
    }, {
        '_id': ObjectId("5c4684645f627debec1dc3db"),
        'email': 'foo_user2@bar.com',
        'first_name': 'Foo_First_name2',
        'is_enabled': True,
        'receive_email': True,
        'company': '',
    }
    ])

    app.data.insert('monitoring', [{
        "_id": ObjectId("5db11ec55f627d8aa0b545fb"),
        "is_enabled": True,
        "users": [
            ObjectId("5c53afa45f627d8333220f15"),
            ObjectId("5c4684645f627debec1dc3db")
        ],
        "company": ObjectId(company_id),
        "subject": "Immediate",
        "name": "W1",
        "_etag": "f023a8db3cdbe31e63ac4b0e6864f5a86ef07253",
        "description": "D3",
        "alert_type": "full_text",
        "query": "headline: (product)",
        "format_type": "monitoring_pdf",
        "schedule": {
            "interval": "immediate"
        }}])


def test_non_admin_actions_fail(client, app):
    user_id = str(PUBLIC_USER_ID)
    with client.session_transaction() as session:
        session['user'] = user_id
        session['name'] = 'public'
        session['user_type'] = 'public'

        response = client.post('/monitoring/new', data=json.dumps({
            "is_enabled": True,
            "users": [
                ObjectId("5c53afa45f627d8333220f15"),
                ObjectId("5c4684645f627debec1dc3db")
            ],
            "company": ObjectId("5c3eb6975f627db90c84093c"),
            "subject": "",
            "name": "W2",
            "_etag": "f023a8db3cdbe31e63ac4b0e6864f5a86ef07253",
            "description": "D3",
            "alert_type": "full_text",
            "query": "hgnhgnhg",
            "schedule": {
                "interval": "immediate"
            }}), content_type='application/json')
        assert response.status_code == 403

        response = client.post('/monitoring/5db11ec55f627d8aa0b545fb/users', data=json.dumps({
                "users": [ObjectId("5c53afa45f627d8333220f15")]}), content_type='application/json')
        assert response.status_code == 403

        response = client.post('/monitoring/5db11ec55f627d8aa0b545fb/schedule', data=json.dumps({
            "schedule": {"interval": "immediate"}}), content_type='application/json')
        assert response.status_code == 403

        response = client.get('/monitoring/schedule_companies')
        assert response.status_code == 403

        response = client.post('/monitoring/5db11ec55f627d8aa0b545fb/users', data=json.dumps({
            "users": [ObjectId("5c53afa45f627d8333220f15")]}), content_type='application/json')
        assert response.status_code == 403


def test_fetch_monitoring(client):
    test_login_succeeds_for_admin(client)
    response = client.get('/monitoring/all')
    assert response.status_code == 200
    items = json.loads(response.get_data())
    assert 1 == len(items)
    assert "5db11ec55f627d8aa0b545fb" == items[0]['_id']


def test_post_monitoring(client):
    test_login_succeeds_for_admin(client)
    response = client.post('/monitoring/new', data=json.dumps({
        "is_enabled": True,
        "users": [
            ObjectId("5c53afa45f627d8333220f15"),
            ObjectId("5c4684645f627debec1dc3db")
        ],
        "company": ObjectId("5c3eb6975f627db90c84093c"),
        "subject": "",
        "name": "W2",
        "_etag": "f023a8db3cdbe31e63ac4b0e6864f5a86ef07253",
        "description": "D3",
        "alert_type": "full_text",
        "query": "hgnhgnhg",
        "schedule": {
            "interval": "immediate"
        }}), content_type='application/json')
    assert response.status_code == 201
    response = client.get('/monitoring/all')
    assert response.status_code == 200
    items = json.loads(response.get_data())
    assert 2 == len(items)
    assert "W1" == items[0]['name']
    assert "W2" == items[1]['name']


def test_set_monitoring_users(client):
    test_login_succeeds_for_admin(client)

    response = client.post('/monitoring/5db11ec55f627d8aa0b545fb/users', data=json.dumps({
            "users": [ObjectId("5c53afa45f627d8333220f15")]}), content_type='application/json')
    assert response.status_code == 200
    response = client.get('/monitoring/all')
    assert response.status_code == 200
    items = json.loads(response.get_data())
    assert 1 == len(items)
    assert ["5c53afa45f627d8333220f15"] == items[0]['users']


def test_set_monitoring_schedule(client):
    test_login_succeeds_for_admin(client)

    response = client.post('/monitoring/5db11ec55f627d8aa0b545fb/schedule', data=json.dumps({
        "schedule": {"interval": "four_hour"}}), content_type='application/json')
    assert response.status_code == 200
    response = client.get('/monitoring/all')
    assert response.status_code == 200
    items = json.loads(response.get_data())
    assert 1 == len(items)
    assert "four_hour" == items[0]['schedule']['interval']


def test_get_companies_with_monitoring_schedules(client):
    test_login_succeeds_for_admin(client)
    response = client.get('/monitoring/schedule_companies')
    assert response.status_code == 200
    items = json.loads(response.get_data())
    assert 1 == len(items)
    assert company_id == items[0]['_id']


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_immediate_alerts(client, app):
    test_login_succeeds_for_admin(client)
    app.data.insert('items', [{
        '_id': 'foo',
        'headline': 'product immediate',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow(),
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run(True)
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_two_hour_alerts(client, app):
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {'schedule': {'interval': 'two_hour'}}, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(days=1)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product last hour',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(minutes=90)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_four_hour_alerts(client, app):
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {'schedule': {'interval': 'four_hour'}}, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(days=1)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product three hours',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(hours=3)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_daily_alerts(client, app):
    now = utcnow()
    now = utc_to_local(app.config['DEFAULT_TIMEZONE'], now)
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {
                        'schedule': {
                            'interval': 'daily',
                            'time': (now - timedelta(minutes=1)).strftime('%H:%M')
                        }
                    }, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(hours=22)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product three hours',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(hours=3)
    }])
    app.data.insert('items', [{
        '_id': 'foo_four_days',
        'headline': 'product four days',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(days=4)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_weekly_alerts(client, app):
    now = utcnow()
    now = utc_to_local(app.config['DEFAULT_TIMEZONE'], now)
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {
                        'schedule': {
                            'interval': 'weekly',
                            'time': (now - timedelta(minutes=1)).strftime('%H:%M'),
                            'day': now.strftime('%a').lower(),
                        }
                    }, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(hours=22)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product three hours',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(hours=3)
    }])
    app.data.insert('items', [{
        '_id': 'foo_four_days',
        'headline': 'product four days',
        'products': [{'code': '12345'}],
        "versioncreated": now - timedelta(days=4)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_send_alerts_respects_last_run_time(client, app):
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {'schedule': {'interval': 'two_hour'}}, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(days=1)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product last hour',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(minutes=90)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 1
        assert outbox[0].recipients == ['foo_user@bar.com', 'foo_user2@bar.com']
        assert outbox[0].sender == 'newsroom@localhost'
        assert outbox[0].subject == 'Immediate'
        assert 'Newsroom Monitoring: W1' in outbox[0].body
        assert 'monitoring-export.pdf' in outbox[0].attachments[0]

    with app.mail.record_messages() as newoutbox:
        w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
        assert w is not None
        assert w.get('last_run_time') is not None
        assert w['last_run_time'] > (utcnow() - timedelta(minutes=5))
        MonitoringEmailAlerts().run()
        assert len(newoutbox) == 0


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_disabled_profile_wont_send_immediate_alerts(client, app):
    test_login_succeeds_for_admin(client)
    get_resource_service('monitoring').patch(ObjectId("5db11ec55f627d8aa0b545fb"), {'is_enabled': False})
    app.data.insert('items', [{
        '_id': 'foo',
        'headline': 'product immediate',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow(),
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run(True)
        assert len(outbox) == 0


@mock.patch('newsroom.email.send_email', mock_send_email)
def test_disabled_profile_wont_send_scheduled_alerts(client, app):
    test_login_succeeds_for_admin(client)
    w = app.data.find_one('monitoring', None, _id='5db11ec55f627d8aa0b545fb')
    assert w is not None
    app.data.update('monitoring', ObjectId('5db11ec55f627d8aa0b545fb'),
                    {'schedule': {'interval': 'two_hour'}, 'is_enabled': False}, w)
    app.data.insert('items', [{
        '_id': 'foo_yesterday',
        'headline': 'product yesterday',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(days=1)
    }])
    app.data.insert('items', [{
        '_id': 'foo_last_hour',
        'headline': 'product last hour',
        'products': [{'code': '12345'}],
        "versioncreated": utcnow() - timedelta(minutes=90)
    }])
    with app.mail.record_messages() as outbox:
        MonitoringEmailAlerts().run()
        assert len(outbox) == 0
