import sys
import os

import pytest
from pytest_bdd import scenarios, when, then, parsers

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from web_scraping.web_scrapping_module_helper import WebScrapperHelper

scenarios('../features/time_converter.feature')

_helper = WebScrapperHelper()


@when(parsers.parse('I convert the time string "{time_str}"'), target_fixture='converted_mins')
def convert_time_string(time_str):
    return _helper.convert_timeStr_to_Mins(time_str)


@then(parsers.parse('the converted minutes are {expected:d}'))
def check_converted_minutes(converted_mins, expected):
    assert converted_mins == expected
