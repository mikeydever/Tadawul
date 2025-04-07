"""
Unit tests for the notifier.email_sender module.
"""

import pytest
import smtplib
from email.message import EmailMessage

from config import settings
from notifier.email_sender import send_email


@pytest.fixture
def mock_smtp(mocker):
    """
    Creates a mock for the smtplib.SMTP class.
    """
    # Create a mock for the SMTP class
    mock_smtp_class = mocker.patch("smtplib.SMTP", autospec=True)
    
    # Configure the mock to return a mock instance
    mock_smtp_instance = mock_smtp_class.return_value
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    
    return mock_smtp_class


@pytest.fixture
def mock_smtp_ssl(mocker):
    """
    Creates a mock for the smtplib.SMTP_SSL class.
    """
    # Create a mock for the SMTP_SSL class
    mock_smtp_ssl_class = mocker.patch("smtplib.SMTP_SSL", autospec=True)
    
    # Configure the mock to return a mock instance
    mock_smtp_ssl_instance = mock_smtp_ssl_class.return_value
    mock_smtp_ssl_instance.__enter__.return_value = mock_smtp_ssl_instance
    
    return mock_smtp_ssl_class


@pytest.fixture
def email_settings(mocker):
    """
    Configures email settings for testing.
    """
    # Mock the settings module to return test values
    mocker.patch.object(settings, "EMAIL_HOST", "smtp.example.com")
    mocker.patch.object(settings, "EMAIL_PORT", 587)
    mocker.patch.object(settings, "EMAIL_USER", "test@example.com")
    mocker.patch.object(settings, "EMAIL_PASSWORD", "password123")
    mocker.patch.object(settings, "EMAIL_SENDER_NAME", "Test Sender")
    mocker.patch.object(settings, "EMAIL_RECIPIENT", "recipient@example.com")


def test_send_email_success_port_587(mock_smtp, email_settings):
    """
    Tests successful email sending using STARTTLS (port 587).
    """
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is True
    assert result is True
    
    # Check that SMTP was called with the correct host and port
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    
    # Get the mock instance
    mock_smtp_instance = mock_smtp.return_value.__enter__.return_value
    
    # Check that the expected methods were called
    mock_smtp_instance.ehlo.assert_called()
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("test@example.com", "password123")
    mock_smtp_instance.send_message.assert_called_once()
    
    # Check that the message was constructed correctly
    sent_message = mock_smtp_instance.send_message.call_args[0][0]
    assert isinstance(sent_message, EmailMessage)
    assert sent_message["Subject"] == "Test Subject"
    assert sent_message["From"] == "Test Sender <test@example.com>"
    assert sent_message["To"] == "recipient@example.com"
    assert sent_message.get_content().strip() == "Test Body"


def test_send_email_success_port_465(mock_smtp_ssl, email_settings, mocker):
    """
    Tests successful email sending using SSL (port 465).
    """
    # Change the port to 465
    mocker.patch.object(settings, "EMAIL_PORT", 465)
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is True
    assert result is True
    
    # Check that SMTP_SSL was called with the correct host and port
    mock_smtp_ssl.assert_called_once()
    
    # Get the mock instance
    mock_smtp_ssl_instance = mock_smtp_ssl.return_value.__enter__.return_value
    
    # Check that the expected methods were called
    mock_smtp_ssl_instance.login.assert_called_once_with("test@example.com", "password123")
    mock_smtp_ssl_instance.send_message.assert_called_once()


def test_send_email_missing_config(email_settings, mocker):
    """
    Tests email sending with missing configuration.
    """
    # Set EMAIL_HOST to an empty string
    mocker.patch.object(settings, "EMAIL_HOST", "")
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is False
    assert result is False


def test_send_email_authentication_error(mock_smtp, email_settings):
    """
    Tests handling of authentication error.
    """
    # Configure the mock to raise an authentication error
    mock_smtp_instance = mock_smtp.return_value.__enter__.return_value
    mock_smtp_instance.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is False
    assert result is False


def test_send_email_connection_error(mock_smtp, email_settings):
    """
    Tests handling of connection error.
    """
    # Configure the mock to raise a connection error
    mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Cannot connect to server")
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is False
    assert result is False


def test_send_email_timeout_error(mock_smtp, email_settings):
    """
    Tests handling of timeout error.
    """
    # Configure the mock to raise a timeout error
    mock_smtp.side_effect = TimeoutError("Connection timed out")
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is False
    assert result is False


def test_send_email_generic_exception(mock_smtp, email_settings):
    """
    Tests handling of generic exception.
    """
    # Configure the mock to raise a generic exception
    mock_smtp.side_effect = Exception("Something went wrong")
    
    # Call the function
    result = send_email(
        subject="Test Subject",
        body="Test Body",
        recipient="recipient@example.com",
    )
    
    # Check that the result is False
    assert result is False