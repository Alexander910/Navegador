"""
test_tcp_connection.py – Pruebas unitarias para tcp_connection.connect_tcp.

Ejecutar:
    python -m unittest -v test_tcp_connection
"""

import unittest
from unittest.mock import patch, MagicMock
import socket
from tcp_connection import connect_tcp, TCPConnectionError


class TestConnectTCPValidation(unittest.TestCase):
    """Pruebas de validación de parámetros de entrada."""

    def test_empty_host_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="", port=80, ip_address="1.2.3.4")

    def test_whitespace_host_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="   ", port=80, ip_address="1.2.3.4")

    def test_invalid_port_zero_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="example.com", port=0, ip_address="1.2.3.4")

    def test_invalid_port_negative_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="example.com", port=-1, ip_address="1.2.3.4")

    def test_invalid_port_too_high_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="example.com", port=70000, ip_address="1.2.3.4")

    def test_empty_ip_raises_error(self):
        with self.assertRaises(TCPConnectionError):
            connect_tcp(host="example.com", port=80, ip_address="")


class TestConnectTCPConnection(unittest.TestCase):
    """Pruebas de la conexión TCP usando mocks."""

    @patch("tcp_connection.socket.socket")
    def test_successful_connection(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock

        result = connect_tcp("example.com", 443, "93.184.216.34")

        mock_socket_cls.assert_called_once_with(
            socket.AF_INET, socket.SOCK_STREAM
        )
        mock_sock.settimeout.assert_called_once()
        mock_sock.connect.assert_called_once_with(("93.184.216.34", 443))
        self.assertEqual(result, mock_sock)

    @patch("tcp_connection.socket.socket")
    def test_timeout_raises_error(self, mock_socket_cls):
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.timeout("timed out")
        mock_socket_cls.return_value = mock_sock

        with self.assertRaises(TCPConnectionError):
            connect_tcp("example.com", 443, "93.184.216.34")


if __name__ == "__main__":
    unittest.main()
