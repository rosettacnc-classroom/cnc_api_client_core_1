"""Utils."""
#-------------------------------------------------------------------------------
# Name:         utils
#
# Purpose:      Utils
#
# Note          Compatible with API server version 1.5.3
#               1 (on 1.x.y) means interface contract
#               x (on 1.x.y) means version
#               y (on 1.x.y) means release
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      03/02/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
# pylint: disable=R0911 -> too-many-return-statements
# pylint: disable=W0718 -> broad-exception-caught           ## take care when you use that ##
#-------------------------------------------------------------------------------
from enum import IntEnum

class DecimalsTrimMode(IntEnum):
    """Xxx..."""
    NONE = 0  # no trimming, so it will keeps all specified decimal places
    FIT = 1   # removes trailing zeros, but retains at least 1 decimal place
    DOT = 2   # removes trailing zeros and retains the decimal point if necessary
    FULL = 3  # removes trailing zeros and the decimal point if they are not needed

def format_float(value: float, decimals: int, trim_mode: DecimalsTrimMode) -> str:
    """
    Formats a float number with advanced decimal handling.

    Args:
        value: The value to format
        decimals: Number of decimals to display
        trim_mode: Trailing zero trim mode (DecimalsTrimMode.*)

    Returns:
        Formatted string

    Examples:
      Value = 1.234, Decimals = 5 -> internally starting from converted float to value 1.23400:
        dtmdNone -> "1.23400"
        dtmdFit  -> "1.234"
        dtmdDot  -> "1.234"
        dtmdFull -> "1.234"

      Value = 1.0, Decimals = 5 -> internally starting from converted float to str value 1.00000:
        dtmdNone -> "1.00000"
        dtmdFit  -> "1.0"
        dtmdDot  -> "1."
        dtmdFull -> "1"

      Value = 1.1, Decimals = 5 -> internally starting from converted float to str value 1.10000:
        dtmdNone -> "1.10000"
        dtmdFit  -> "1.1"
        dtmdDot  -> "1.1"
        dtmdFull -> "1.1"

      Value = 0.0, Decimals = 5 -> internally starting from converted float to str value 0.00000:
        dtmdNone -> "0.00000"
        dtmdFit  -> "0.0"
        dtmdDot  -> "0."
        dtmdFull -> "0"
    """
    try:
        result = f"{value:.{decimals}f}"
        if trim_mode == DecimalsTrimMode.NONE:
            return result
        dot_pos = result.find('.')
        if dot_pos == -1:
            return result
        for i in range(len(result) - 1, dot_pos, -1):
            if result[i] != '0':
                return result[:i + 1]
        if trim_mode == DecimalsTrimMode.FIT:
            return result[:dot_pos + 2]
        if trim_mode == DecimalsTrimMode.DOT:
            return result[:dot_pos + 1]
        if trim_mode == DecimalsTrimMode.FULL:
            return result[:dot_pos]
        return result
    except Exception:
        return ''

def is_in_str_list_range(texts, index):
    """Checks if index in range of a list of strings."""
    return 0 <= index <= len(texts)
    #return index >= 0 and index <= len(texts)
