from unittest.mock import Mock, patch

from .index import handler


class TestHandler:
    @patch("index.update_legislation_table")
    def test_handler(
        self,
        mock_update_legislation_table,
    ):
        """
        Given an event dict with an integer trigger_date and context
        When the handler function is called with them
        Then the update_legislation_table function should be called
            with the trigger_date
        """
        event = {"trigger_date": 7}
        context = Mock()
        handler(event, context)
        mock_update_legislation_table.assert_called_with(7)

    @patch("index.update_legislation_table")
    def test_handler_non_integer_trigger_date(
        self,
        mock_update_legislation_table,
    ):
        """
        Given an event dict with a non-integer trigger_date and context
        When the handler function is called with them
        Then the update_legislation_table function should be called with None
        """
        event = {"trigger_date": "3 weeks ago?"}
        context = Mock()
        handler(event, context)
        mock_update_legislation_table.assert_called_with(None)

    @patch("index.update_legislation_table")
    def test_handler_no_trigger_date(
        self,
        mock_update_legislation_table,
    ):
        """
        Given an event dict with a no trigger_date field and context
        When the handler function is called with them
        Then the update_legislation_table function should be called with None
        """
        event: dict = {}
        context = Mock()
        handler(event, context)
        mock_update_legislation_table.assert_called_with(None)
