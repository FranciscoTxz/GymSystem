import logging

from common.log_helper import get_logger


def test_get_logger_sets_requested_level():
    module_logger = get_logger("test.explicit", logging.DEBUG)

    assert module_logger.name == "common.log_helper.test.explicit"
    assert module_logger.level == logging.DEBUG


def test_get_logger_preserves_level_when_zero_requested():
    module_logger = get_logger("test.zero", logging.NOTSET)

    assert module_logger.level == logging.NOTSET
