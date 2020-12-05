import unittest
import mock
import binascii
import datetime
import base64
from uuid import UUID

try:
    from urllib.parse import ParseResult
except ImportError:
    from urlparse import ParseResult

import upnpclient as upnp


class TestUPnPClient(unittest.TestCase):
    @mock.patch("upnpclient.ssdp.Device", return_value="test string")
    @mock.patch("upnpclient.ssdp.scan")
    def test_discover(self, mock_scan, mock_server):
        """
        discover() should call netdisco's scan function and return a list of unique servers.
        """
        url = "http://www.example.com"
        entry = mock.Mock()
        entry.location = url
        mock_scan.return_value = [entry, entry]
        ret = upnp.discover()
        mock_scan.assert_called()
        mock_server.assert_called_with(url)
        self.assertEqual(ret, ["test string"])

    @mock.patch("upnpclient.ssdp.Device", side_effect=Exception)
    @mock.patch("upnpclient.ssdp.scan")
    def test_discover_exception(self, mock_scan, mock_server):
        """
        If unable to read a discovered server's root XML file, it should not appear in the list.
        """
        url = "http://www.example.com"
        entry = mock.Mock()
        entry.location = url
        mock_scan.return_value = [entry]
        ret = upnp.discover()
        mock_scan.assert_called()
        mock_server.assert_called_with(url)
        self.assertEqual(ret, [])

    def test_validate_date(self):
        """
        Should validate the 'date' type.
        """
        ret = upnp.Action.validate_arg("2017-08-11", dict(datatype="date"))
        self.assertEqual(ret, (True, set()))

    def test_validate_bad_date(self):
        """
        Bad 'date' type should fail validation.
        """
        valid, reasons = upnp.Action.validate_arg("2017-13-13", dict(datatype="date"))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_validate_date_with_time(self):
        """
        Should raise a ValidationError if a 'date' contains a time.
        """
        valid, reasons = upnp.Action.validate_arg(
            "2017-13-13T12:34:56", dict(datatype="date")
        )
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_date(self):
        """
        Should parse a valid date into a `datetime.date` object.
        """
        marshalled, val = upnp.marshal.marshal_value("date", "2017-08-11")
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.date)
        tests = dict(year=2017, month=8, day=11)
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)

    def test_marshal_datetime(self):
        """
        Should parse and marshal a 'dateTime' into a timezone naive `datetime.datetime`.
        """
        marshalled, val = upnp.marshal.marshal_value("dateTime", "2017-08-11T12:34:56")
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.datetime)
        tests = dict(year=2017, month=8, day=11, hour=12, minute=34, second=56)
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.tzinfo, None)

    def test_marshal_datetime_tz(self):
        """
        Should parse and marshal a 'dateTime.tz' into a timezone aware `datetime.datetime`.
        """
        marshalled, val = upnp.marshal.marshal_value(
            "dateTime.tz", "2017-08-11T12:34:56+1:00"
        )
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.datetime)
        tests = dict(year=2017, month=8, day=11, hour=12, minute=34, second=56)
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.utcoffset(), datetime.timedelta(hours=1))

    def test_validate_time_illegal_tz(self):
        """
        Should fail validation if 'time' contains a timezone.
        """
        valid, reasons = upnp.Action.validate_arg("12:34:56+1:00", dict(datatype="time"))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_time(self):
        """
        Should parse a 'time' into a timezone naive `datetime.time`.
        """
        marshalled, val = upnp.marshal.marshal_value("time", "12:34:56")
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.time)
        tests = dict(hour=12, minute=34, second=56)
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.tzinfo, None)

    def test_marshal_time_tz(self):
        """
        Should parse a 'time.tz' into a timezone aware `datetime.time`.
        """
        marshalled, val = upnp.marshal.marshal_value("time.tz", "12:34:56+1:00")
        self.assertTrue(marshalled)
        self.assertIsInstance(val, datetime.time)
        tests = dict(hour=12, minute=34, second=56)
        for key, value in tests.items():
            self.assertEqual(getattr(val, key), value)
        self.assertEqual(val.utcoffset(), datetime.timedelta(hours=1))

    def test_marshal_bool(self):
        """
        Should parse a 'boolean' into a `bool`.
        """
        valid_true = ("1", "true", "TRUE", "True", "yes", "YES", "Yes")
        valid_false = ("0", "false", "FALSE", "False", "no", "NO", "No")
        tests = list(zip(valid_true, [True] * len(valid_true))) + list(
            zip(valid_false, [False] * len(valid_false))
        )
        for item, test in tests:
            marshalled, val = upnp.marshal.marshal_value("boolean", item)
            self.assertTrue(marshalled)
            self.assertEqual(val, test)

    def test_validate_bad_bool(self):
        """
        Should raise a ValidationError if an invalid 'boolean' is provided.
        """
        valid, reasons = upnp.Action.validate_arg("2", dict(datatype="boolean"))
        print(reasons)
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_validate_base64(self):
        """
        Should validate a 'bin.base64' value.
        """
        bstring = "Hello, World!".encode("utf8")
        encoded = base64.b64encode(bstring)
        valid, reasons = upnp.Action.validate_arg(encoded, dict(datatype="bin.base64"))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_base64(self):
        """
        Should simply leave the base64 string as it is.
        """
        bstring = "Hello, World!".encode("utf8")
        encoded = base64.b64encode(bstring)
        marshalled, val = upnp.marshal.marshal_value("bin.base64", encoded)
        self.assertTrue(marshalled)
        self.assertEqual(val, encoded)

    def test_validate_hex(self):
        """
        Should validate a 'bin.hex' value.
        """
        bstring = "Hello, World!".encode("ascii")
        valid, reasons = upnp.Action.validate_arg(
            binascii.hexlify(bstring), dict(datatype="bin.hex")
        )
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_hex(self):
        """
        Should simply leave the hex string as it is.
        """
        bstring = "Hello, World!".encode("ascii")
        encoded = binascii.hexlify(bstring)
        marshalled, val = upnp.marshal.marshal_value("bin.hex", encoded)
        self.assertTrue(marshalled)
        self.assertEqual(val, encoded)

    def test_validate_uri(self):
        """
        Should validate a 'uri' value.
        """
        uri = "https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable"
        valid, reasons = upnp.Action.validate_arg(uri, dict(datatype="uri"))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_marshal_uri(self):
        """
        Should parse a 'uri' value into a `ParseResult`.
        """
        uri = "https://media.giphy.com/media/22kxQ12cxyEww/giphy.gif?something=variable"
        marshalled, val = upnp.marshal.marshal_value("uri", uri)
        self.assertTrue(marshalled)
        self.assertIsInstance(val, ParseResult)

    def test_validate_uuid(self):
        """
        Should validate a 'uuid' value.
        """
        uuid = "bec6d681-a6af-4e7d-8b31-bcb78018c814"
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype="uuid"))
        print(reasons)
        self.assertFalse(reasons)
        self.assertTrue(valid)

    def test_validate_bad_uuid(self):
        """
        Should reject badly formatted 'uuid' values.
        """
        uuid = "bec-6d681a6af-4e7d-8b31-bcb78018c814"
        valid, reasons = upnp.Action.validate_arg(uuid, dict(datatype="uuid"))
        self.assertTrue(reasons)
        self.assertFalse(valid)

    def test_marshal_uuid(self):
        """
        Should parse a 'uuid' into a `uuid.UUID`.
        """
        uuid = "bec6d681-a6af-4e7d-8b31-bcb78018c814"
        marshalled, val = upnp.marshal.marshal_value("uuid", uuid)
        self.assertTrue(marshalled)
        self.assertIsInstance(val, UUID)

    def test_validate_subscription_response(self):
        """
        Should validate the sub response and return sid and timeout.
        """
        sid = "abcdef"
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout="Second-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_response_caps(self):
        """
        Should validate the sub response and return sid and timeout regardless of capitalisation.
        """
        sid = "abcdef"
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(sid=sid, TIMEOUT="SeCoNd-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_response_infinite(self):
        """
        Should validate the sub response and return None as the timeout.
        """
        sid = "abcdef"
        timeout = "infinite"
        resp = mock.Mock()
        resp.headers = dict(SID=sid, Timeout="Second-%s" % timeout)
        rsid, rtimeout = upnp.Service.validate_subscription_response(resp)
        self.assertEqual(rsid, sid)
        self.assertEqual(rtimeout, None)

    def test_validate_subscription_response_no_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is missing.
        """
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef")
        self.assertRaises(
            upnp.UnexpectedResponse, upnp.Service.validate_subscription_response, resp
        )

    def test_validate_subscription_response_no_sid(self):
        """
        Should raise UnexpectedResponse if sid is missing.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-123")
        self.assertRaises(
            upnp.UnexpectedResponse, upnp.Service.validate_subscription_response, resp
        )

    def test_validate_subscription_response_bad_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is in the wrong format.
        """
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef", Timeout="123")
        self.assertRaises(
            upnp.UnexpectedResponse, upnp.Service.validate_subscription_response, resp
        )

    def test_validate_subscription_response_bad_timeout2(self):
        """
        Should raise UnexpectedResponse if timeout is not an int/infinite.
        """
        resp = mock.Mock()
        resp.headers = dict(SID="abcdef", Timeout="Second-abc")
        self.assertRaises(
            upnp.UnexpectedResponse, upnp.Service.validate_subscription_response, resp
        )

    def test_validate_subscription_renewal_response(self):
        """
        Should validate the sub renewal response and return the timeout.
        """
        timeout = 123
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-%s" % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        self.assertEqual(rtimeout, timeout)

    def test_validate_subscription_renewal_response_infinite(self):
        """
        Should validate the sub renewal response and return None as the timeout.
        """
        timeout = "infinite"
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-%s" % timeout)
        rtimeout = upnp.Service.validate_subscription_renewal_response(resp)
        self.assertEqual(rtimeout, None)

    def test_validate_subscription_renewal_response_no_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is missing.
        """
        resp = mock.Mock()
        resp.headers = dict()
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp,
        )

    def test_validate_subscription_renewal_response_bad_timeout(self):
        """
        Should raise UnexpectedResponse if timeout is in the wrong format.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout="123")
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp,
        )

    def test_validate_subscription_renewal_response_bad_timeout2(self):
        """
        Should raise UnexpectedResponse if timeout is not an int/infinite.
        """
        resp = mock.Mock()
        resp.headers = dict(Timeout="Second-abc")
        self.assertRaises(
            upnp.UnexpectedResponse,
            upnp.Service.validate_subscription_renewal_response,
            resp,
        )
