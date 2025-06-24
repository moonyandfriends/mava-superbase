"""Tests for mava_sync.py"""

import importlib
import os
from unittest.mock import Mock, patch

import pytest

import mava_sync
from mava_sync import (
    fetch_page,
    health_check,
    process_tickets_batch,
    sync_all_pages,
    upsert_to_table,
)


@pytest.fixture
def mock_session():
    """Mock requests session"""
    session = Mock()
    return session


@pytest.fixture
def sample_tickets():
    """Sample ticket data for testing"""
    return [
        {
            "_id": "1",
            "status": "open",
            "customer": {"_id": "cust1", "name": "Test Customer"},
            "messages": [{"_id": "msg1", "content": "Test message"}],
            "attributes": [
                {"_id": "attr1", "attribute": "test_attr", "content": "test_value"}
            ],
        },
        {
            "_id": "2",
            "status": "closed",
            "customer": {"_id": "cust2", "name": "Test Customer 2"},
            "messages": [],
            "attributes": [],
        },
    ]


@patch("mava_sync.test_mava_auth")
@patch("mava_sync.get_supabase_client")
def test_health_check_success(mock_get_client, mock_test_auth):
    """Test successful health check"""
    mock_supabase = Mock()
    mock_get_client.return_value = mock_supabase
    mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        Mock()
    )
    mock_test_auth.return_value = True

    result = health_check()

    assert result is True
    mock_supabase.table.assert_called_once_with("tickets")


@patch("mava_sync.test_mava_auth")
@patch("mava_sync.get_supabase_client")
def test_health_check_failure(mock_get_client, mock_test_auth):
    """Test failed health check"""
    mock_supabase = Mock()
    mock_get_client.return_value = mock_supabase
    mock_supabase.table.side_effect = Exception("Connection error")
    mock_test_auth.return_value = True

    result = health_check()

    assert result is False


def test_fetch_page_success(mock_session, sample_tickets):
    """Test successful API page fetch"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tickets": sample_tickets}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets
    mock_session.get.assert_called_once()


def test_fetch_page_with_data_field(mock_session, sample_tickets):
    """Test API page fetch with 'data' field"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": sample_tickets}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets


def test_fetch_page_direct_array(mock_session, sample_tickets):
    """Test API page fetch with direct array response"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = sample_tickets
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets


@patch("mava_sync.get_supabase_client")
def test_upsert_to_table_success(mock_get_client):
    """Test successful table upsert"""
    mock_supabase = Mock()
    mock_get_client.return_value = mock_supabase
    mock_resp = Mock()
    mock_resp.data = [{"id": "1"}]
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
        mock_resp
    )

    sample_records = [{"id": "1", "name": "Test"}]

    # Should not raise any exception
    upsert_to_table("test_table", sample_records)

    mock_supabase.table.assert_called_once_with("test_table")


@patch("mava_sync.get_supabase_client")
def test_upsert_to_table_empty_list(mock_get_client):
    """Test upsert with empty record list"""
    upsert_to_table("test_table", [])

    # Should not call supabase at all
    mock_get_client.assert_not_called()


@patch("mava_sync.get_supabase_client")
def test_upsert_to_table_failure(mock_get_client):
    """Test failed table upsert"""
    mock_supabase = Mock()
    mock_get_client.return_value = mock_supabase
    mock_resp = Mock()
    mock_resp.data = None
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
        mock_resp
    )

    sample_records = [{"id": "1", "name": "Test"}]

    # Should not raise any exception, just log the error
    upsert_to_table("test_table", sample_records)

    # Verify that the function attempted to upsert
    mock_supabase.table.assert_called_once_with("test_table")


@patch("mava_sync.upsert_to_table")
def test_process_tickets_batch(mock_upsert, sample_tickets):
    """Test ticket batch processing"""
    process_tickets_batch(sample_tickets)

    # Should call upsert_to_table for each table type
    expected_calls = [
        "customers",
        "tickets",
        "messages",
        "ticket_attributes",
        "customer_attributes",
    ]
    actual_calls = [call[0][0] for call in mock_upsert.call_args_list]

    for expected_table in expected_calls:
        assert expected_table in actual_calls


@patch("mava_sync.fetch_page")
@patch("mava_sync.process_tickets_batch")
@patch("requests.Session")
def test_sync_all_pages(mock_session_class, mock_process, mock_fetch, sample_tickets):
    """Test complete sync process"""
    mock_session = Mock()
    mock_session_class.return_value = mock_session

    # First call returns tickets, second call returns empty (end of pagination)
    mock_fetch.side_effect = [sample_tickets, []]

    sync_all_pages()

    assert mock_fetch.call_count == 2
    mock_process.assert_called_once_with(sample_tickets)


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock required environment variables"""
    with patch.dict(
        os.environ,
        {
            "MAVA_AUTH_TOKEN": "test_token",
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_SERVICE_KEY": "test_key",
            "PAGE_SIZE": "50",
            "LOG_LEVEL": "INFO",
        },
    ):
        yield


class TestEnvironmentVariables:
    """Test environment variable handling"""

    def test_missing_required_vars(self):
        """Test behavior when required environment variables are missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                importlib.reload(mava_sync)

    def test_optional_vars_defaults(self):
        """Test that optional variables have proper defaults"""
        with patch.dict(
            os.environ,
            {
                "MAVA_AUTH_TOKEN": "test_token",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_SERVICE_KEY": "test_key",
            },
            clear=True,
        ):
            importlib.reload(mava_sync)

            assert mava_sync.PAGE_SIZE == 50
            assert mava_sync.LOG_LEVEL == "INFO"
