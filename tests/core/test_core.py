import pytest
from unittest.mock import MagicMock, patch
from spotisync.core.config import read_create_config
from spotisync.core.scheduler import run_scheduler

def test_read_create_config():
    config = read_create_config()
    assert config is not None
    assert config.has_section('spotipy')
    assert config.has_section('settings')

@patch('spotisync.core.scheduler.schedule')
@patch('spotisync.core.scheduler.sleep')
@patch('spotisync.core.scheduler.fetch_user_lib_and_save_all')
def test_run_scheduler(mock_fetch, mock_sleep, mock_schedule):
    # Mock config
    mock_config = MagicMock()
    mock_config.__getitem__.return_value = {'schedule_time': '30'}
    
    with patch('spotisync.core.scheduler.read_create_config', return_value=mock_config):
        # Set up a side effect to break the infinite loop
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        
        # Run the scheduler
        with pytest.raises(KeyboardInterrupt):
            run_scheduler(debug=True)
        
        # Verify the scheduler was set up correctly
        mock_schedule.every.assert_called_once_with(30)
        mock_fetch.assert_called_once_with()
        assert mock_sleep.call_count >= 1