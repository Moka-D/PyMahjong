"""jongpy.core.exceptions"""


class JongPyError(Exception):
    """jonpyモジュール汎用例外"""
    pass


class InvalidOperationError(JongPyError):
    """不正な操作"""
    pass


class PaiFormatError(JongPyError):
    """不正な牌文字列"""
    pass


class PaiOverFlowError(JongPyError):
    """5枚目の牌が存在"""
    pass


class PaiNotExistError(JongPyError):
    """指定の牌が存在しない"""
    pass


class MianziFormatError(JongPyError):
    """不正な面子文字列"""
    pass


class ShoupaiOverFlowError(JongPyError):
    """多牌"""
    pass


class ShoupaiUnderFlowError(JongPyError):
    """少牌"""
    pass
