import pytest
from jongpy.core.shoupai import Shoupai
from jongpy.core.hule import hule_mianzi, hule_mianzi_jiulian


class TestHule:

    def test_hule_mianzi_normal_1(self):
        shoupai = Shoupai.from_string('m2234450p234s234m3')
        expected = [
            ['m22', 'm3_!45', 'm345', 'p234', 's234'],
            ['m55', 'm23_!4', 'm234', 'p234', 's234']
        ]
        actual = hule_mianzi(shoupai)
        assert actual == expected

    def test_hule_mianzi_normal_2(self):
        shoupai = Shoupai.from_string('m111222333p8999p7')
        expected = [
            ['p99', 'm123', 'm123', 'm123', 'p7_!89'],
            ['p99', 'm111', 'm222', 'm333', 'p7_!89']
        ]
        actual = hule_mianzi(shoupai)
        assert actual == expected

    def test_hule_mianzi_normal_3(self):
        shoupai = Shoupai.from_string('m12334p567s88z777')
        expected = [
            ['s88', 'm12=!3', 'm234', 'p567', 'z777'],
            ['s88', 'm123', 'm2=!34', 'p567', 'z777']
        ]
        actual = hule_mianzi(shoupai, 'm2=')
        assert actual == expected

    def test_hule_mianzi_goushi(self):
        shoupai = Shoupai.from_string('m19p19s19z1235567z4')
        expected = [['z55', 'm1', 'm9', 'p1', 'p9', 's1', 's9', 'z1', 'z2', 'z3', 'z4_!', 'z6', 'z7']]
        actual = hule_mianzi(shoupai)
        assert actual == expected

    def test_hule_mianzi_qudui(self):
        shoupai = Shoupai.from_string('m225099p1133s8z22s8')
        expected = [['m22', 'm55', 'm99', 'p11', 'p33', 's88_!', 'z22']]
        actual = hule_mianzi(shoupai)
        assert actual == expected

    def test_hule_mianzi_normal_qidui(self):
        shoupai = Shoupai.from_string('m223344p506677s88')
        expected = [
            ['s88_!', 'm234', 'm234', 'p567', 'p567'],
            ['m22', 'm33', 'm44', 'p55', 'p66', 'p77', 's88_!']
        ]
        actual = hule_mianzi(shoupai)
        assert actual == expected

    def test_hule_mianzi_jiulian(self):
        shoupai = Shoupai.from_string('m1112345678999m1')
        expected = [['m11123456789991_!']]
        actual = hule_mianzi_jiulian(shoupai, 'm1_')
        assert actual == expected
