import base64
import binascii
import datetime
from unittest import mock
from uuid import UUID

import pytest
from urllib.parse import ParseResult

import upnpclient as upnp


# --- Date/Time validation and marshalling ---


class TestValidateDate:
    def test_validate_date(self):
        """Should validate the 'date' type."""
        ret = upnp.Action.validate_arg("2017-08-11", dict(datatype="date"))
        assert ret == (True, set())

    def test_validate_bad_date(self):
        """Bad 'date' type should fail validation."""
        valid, reasons = upnp.Action.validate_arg("2017-13-13", dict(datatype="date"))
        assert reasons
        assert not valid

    def test_validate_date_with_time(self):
        """Should raise a ValidationError if a 'date' contains a time."""
        valid, reasons = upnp.Action.validate_arg(
            "2017-13-13T12:34:56", dict(datatype="date")
        )
        assert reasons
        assert not valid


class TestMarshalDate:
    def test_marshal_date(self):
        """Should parse a valid date into a `datetime.date` object."""
        marshalled, val = upnp.marshal.marshal_value("date", "2017-08-11")
        assert marshalled
        assert isinstance(val, datetime.date)
        assert val.year == 2017
        assert val.month == 8
        assert val.day == 11

    def test_marshal_datetime(self):
        """Should parse and marshal a 'dateTime' into a timezone naive `datetime.datetime`."""
        marshalled, val = upnp.marshal.marshal_value("dateTime", "2017-08-11T12:34:56")
        assert marshalled
        assert isinstance(val, datetime.datetime)
        assert val.year == 2017
        assert val.month == 8
        assert val.day == 11
        assert val.hour == 12
        assert val.minute == 34
        assert val.second == 56
        assert val.tzinfo is None

    def test_marshal_datetime_tz(self):
        """Should parse and marshal a 'dateTime.tz' into a timezone aware `datetime.datetime`."""
        marshalled, val = upnp.marshal.marshal_value(
            "dateTime.tz", "2017-08-11T12:34:56+1:00"
        )
        assert marshalled
        assert isinstance(val, datetime.datetime)
        assert val.year == 2017
        assert val.month == 8
        assert val.day == 11
        assert val.hour == 12
        assert val.minute == 34
        assert val.second == 56
        assert val.utcoffset() == datetime.timedelta(hours=1)


class TestValidateTime:
    def test_validate_time_illegal_tz(self):
        """Should fail validation if 'time' contains a timezone."""
        valid, reasons = upnp.Action.validate_arg("12:34:56+1:00", dict(datatype="time"))
        assert reasons
        assert not valid


class TestMarshalTime:
    def test_marshal_time(self):
        """Should parse a 'time' into a timezone naive `datetime.time`."""
        marshalled, val = upnp.marshal.marshal_value("time", "12:34:56")
        assert marshalled
        assert isinstance(val, datetime.time)
        assert val.hour == 12
        assert val.minute == 34
        assert val.second == 56
        assert val.tzinfo is None

    def test_marshal_time_tz(self):
        """Should parse a 'time.tz' into a timezone aware `datetime.time`."""
        marshalled, val = upnp.marshal.marshal_value("time.tz", "12:34:56+1:00")
        assert marshalled
        assert isinstance(val, datetime.time)
        assert val.hour == 12
        assert val.minute == 34
        assert val.second == 56
        assert val.utcoffset() == datetime.timedelta(hours=1)


# --- Boolean ---


class TestMarshalBool:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1", True),
            ("true", True),
            ("TRUE", True),
            ("True", True),
            ("yes", True),
            ("YES", True),
            ("Yes", True),
            ("0", False),
            ("false", False),
            ("FALSE", False),
            ("False", False),
            ("no", False),
            ("NO", False),
            ("No", False),
        ],
    )
    def test_marshal_bool(self, value, expected):
        """Should parse a 'boolean' into a `bool`."""
        marshalled, val = upnp.marshal.marshal_value("boolean", value)
        assert marshalled
        assert val == expected

    def test_validate_bad_bool(self):
        """Should raise a ValidationError if an invalid 'boolean' is provided."""
        valid, reasons = upnp.Action.validate_arg("2", dict(datatype="boolean"))
        assert reasons
        assert not valid


# --- Base64 ---


class TestBase64:
    def test_validate_base64(self):
        """Should validate a 'bin.base64' value."""
        bstring = "Hello, World!".encode("utf8")
        encoded = base64.b64encode(bstring)
        valid, reasons = upnp.Action.validate_arg(encoded, dict(datatype="bin.base64"))
        assert not reasons
        assert valid

    def test_marshal_base64(self):
        """Should simply leave the base64 string as it is."""
        bstring = "Hello, World!".encode("utf8")
        encoded = base64.b64encode(bstring)
        marshalled, val = upnp.marshal.marshal_value("bin.base64", encoded)
        assert marshalled
        assert val == encoded


# --- Hex ---


class TestHex:
    def test_validate_hex(self):
        """Should validate a 'bin.hex' value."""
        bstring = "Hello, World!".encode("ascii")
        valid, reasons = upnp.Action.validate_arg(
            binascii.hexlify(bstring), dict(datatype="bin.hex")
        )
        assert not reasons
        assert valid

    def test_marshal_hex(self):
        """Should simply leave the hex string as it is."""
        bstring = "Hello, World!".encode("ascii")
        encoded = binascii.hexlify(bstring)
        marshalled, val = upnp.marshal.marshal_value("bin.hex", encoded)
        assert marshalled
        assert val == encoded


# --- URI ---


class TestURI:
    def test_validate_uri(self):
        """Should validate a 'uri' value."""
        uri = "https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable"
        valid, reasons = upnp.Action.validate_arg(uri, dict(datatype="uri"))
        assert not reasons
        assert valid

    def test_marshal_uri(self):
        """Should parse a 'uri' value into a `ParseResult`."""
        uri = "https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable"
        marshalled, val = upnp.marshal.marshal_value("uri", uri)
        assert marshalled
        assert isinstance(val, ParseResult)


# --- UUID ---


class TestUUID:
    def test_validate_uuid(self):
        """Should validate a 'uuid' value."""
        uuid = "bec6d681-a6af-4e7d-8b31-bcb78018c814"
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype="uuid"))
        assert not reasons
        assert valid

    def test_validate_bad_uuid(self):
        """Should reject badly formatted 'uuid' values."""
        uuid = "bec-6d681a6af-4e7d-8b31-bcb78018c814"
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype="uuid"))
        assert reasons
        assert not valid

    def test_marshal_uuid(self):
        """Should parse a 'uuid' into a `uuid.UUID`."""
        uuid = "bec6d681-a6af-4e7d-8b31-bcb78018c814"
        marshalled, val = upnp.marshal.marshal_value("uuid", uuid)
        assert marshalled
        assert isinstance(val, UUID)


# --- Subscription validation ---


class TestValidateSubscriptionResponse:
    def test_validate_subscription_response(self):
        """Should validate the sub response and return sid and timeout."""
        sid = "abcdef"
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout="Second-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        assert rsid == sid
        assert rtimeout == timeout

    def test_validate_subscription_response_caps(self):
        """Should validate the sub response and return sid and timeout regardless of capitalisation."""
        sid = "abcdef"
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(sid=sid, TIMEOUT="SeCoNd-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        assert rsid == sid
        assert rtimeout == timeout

    def test_validate_subscription_response_infinite(self):
        """Should validate the sub response and return None as the timeout."""
        sid = "abcdef"
        timeout = "infinite"
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout="Second-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        assert rsid == sid
        assert rtimeout is None

    def test_validate_subscription_response_no_timeout(self):
        """Should raise UnexpectedResponse if timeout is missing."""
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_response(resp)

    def test_validate_subscription_response_no_sid(self):
        """Should raise UnexpectedResponse if sid is missing."""
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-123")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_response(resp)

    def test_validate_subscription_response_bad_timeout(self):
        """Should raise UnexpectedResponse if timeout is in the wrong format."""
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef", Timeout="123")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_response(resp)

    def test_validate_subscription_response_bad_timeout2(self):
        """Should raise UnexpectedResponse if timeout is not an int/infinite."""
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef", Timeout="Second-abc")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_response(resp)


class TestValidateSubscriptionRenewalResponse:
    def test_validate_subscription_renewal_response(self):
        """Should validate the sub renewal response and return the timeout."""
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-%s" % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        assert rtimeout == timeout

    def test_validate_subscription_renewal_response_infinite(self):
        """Should validate the sub renewal response and return None as the timeout."""
        timeout = "infinite"
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-%s" % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        assert rtimeout is None

    def test_validate_subscription_renewal_response_no_timeout(self):
        """Should raise UnexpectedResponse if timeout is missing."""
        resp = mock.Mock()
        resp.headers = dict()
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_renewal_response(resp)

    def test_validate_subscription_renewal_response_bad_timeout(self):
        """Should raise UnexpectedResponse if timeout is in the wrong format."""
        resp = mock.Mock()
        resp.headers = dict(Timeout="123")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_renewal_response(resp)

    def test_validate_subscription_renewal_response_bad_timeout2(self):
        """Should raise UnexpectedResponse if timeout is not an int/infinite."""
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-abc")
        with pytest.raises(upnp.UnexpectedResponse):
            upnp.Service.validate_subscription_renewal_response(resp)
