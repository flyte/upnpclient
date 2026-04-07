from unittest.mock import patch, Mock
import upnpclient


def test_discover():
    """discover() should call scan and return unique devices."""
    with patch("upnpclient.ssdp.Device", return_value="test string") as mock_device, \
         patch("upnpclient.ssdp.scan") as mock_scan:
        url = "http://www.example.com"
        entry = Mock()
        entry.location = url
        mock_scan.return_value = [entry, entry]
        ret = upnpclient.discover()
        mock_scan.assert_called()
        mock_device.assert_called_with(url)
        assert ret == ["test string"]


def test_discover_exception():
    """If unable to read a server's XML, it should not appear in results."""
    with patch("upnpclient.ssdp.Device", side_effect=Exception) as mock_device, \
         patch("upnpclient.ssdp.scan") as mock_scan:
        url = "http://www.example.com"
        entry = Mock()
        entry.location = url
        mock_scan.return_value = [entry]
        ret = upnpclient.discover()
        mock_scan.assert_called()
        mock_device.assert_called_with(url)
        assert ret == []
