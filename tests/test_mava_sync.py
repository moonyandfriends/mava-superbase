"""Tests for mava_sync.py"""

import importlib
import os
from unittest.mock import Mock, patch

import pytest

import mava_sync
from mava_sync import fetch_page, health_check, sync_all_pages, upsert_tickets


@pytest.fixture
def mock_session():
    """Mock requests session"""
    session = Mock()
    return session


@pytest.fixture
def sample_tickets():
    """Sample ticket data for testing"""
    return [
        {"id": "1", "title": "Test Ticket 1", "status": "open"},
        {"id": "2", "title": "Test Ticket 2", "status": "closed"},
    ]


@patch("mava_sync.supabase")
def test_health_check_success(mock_supabase):
    """Test successful health check"""
    mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = (
        Mock()
    )

    result = health_check()

    assert result is True
    mock_supabase.table.assert_called_once_with("tickets")


@patch("mava_sync.supabase")
def test_health_check_failure(mock_supabase):
    """Test failed health check"""
    mock_supabase.table.side_effect = Exception("Connection error")

    result = health_check()

    assert result is False


def test_fetch_page_success(mock_session, sample_tickets):
    """Test successful API page fetch"""
    mock_response = Mock()
    mock_response.json.return_value = {"tickets": sample_tickets}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets
    mock_session.get.assert_called_once()


def test_fetch_page_with_data_field(mock_session, sample_tickets):
    """Test API page fetch with 'data' field"""
    mock_response = Mock()
    mock_response.json.return_value = {"data": sample_tickets}
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets


def test_fetch_page_direct_array(mock_session, sample_tickets):
    """Test API page fetch with direct array response"""
    mock_response = Mock()
    mock_response.json.return_value = sample_tickets
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response

    result = fetch_page(mock_session, skip=0)

    assert result == sample_tickets


@patch("mava_sync.supabase")
def test_upsert_tickets_success(mock_supabase, sample_tickets):
    """Test successful ticket upsert"""
    mock_resp = Mock()
    mock_resp.data = sample_tickets
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
        mock_resp
    )

    # Should not raise any exception
    upsert_tickets(sample_tickets)

    mock_supabase.table.assert_called_once_with("tickets")


@patch("mava_sync.supabase")
def test_upsert_tickets_empty_list(mock_supabase):
    """Test upsert with empty ticket list"""
    upsert_tickets([])

    # Should not call supabase at all
    mock_supabase.table.assert_not_called()


@patch("mava_sync.supabase")
def test_upsert_tickets_failure(mock_supabase, sample_tickets):
    """Test failed ticket upsert"""
    mock_resp = Mock()
    mock_resp.data = None
    mock_supabase.table.return_value.upsert.return_value.execute.return_value = (
        mock_resp
    )

    with pytest.raises(RuntimeError, match="Supabase upsert failed"):
        upsert_tickets(sample_tickets)


@patch("mava_sync.fetch_page")
@patch("mava_sync.upsert_tickets")
@patch("requests.Session")
def test_sync_all_pages(mock_session_class, mock_upsert, mock_fetch, sample_tickets):
    """Test complete sync process"""
    mock_session = Mock()
    mock_session_class.return_value = mock_session

    # First call returns tickets, second call returns empty (end of pagination)
    mock_fetch.side_effect = [sample_tickets, []]

    sync_all_pages()

    assert mock_fetch.call_count == 2
    mock_upsert.assert_called_once_with(sample_tickets)


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
