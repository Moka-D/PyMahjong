import pytest   # noqa

from jongpy.core.shoupai import Shoupai
from jongpy.core.hule import hule_mianzi


class TestHuleMianzi:

    def test_normal_zimo(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055s789z11122'), None)
                == [['z22_!', 'm123', 'p555', 's789', 'z111']])

    def test_normal_rong(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055s789z1112'), 'z2+')
                == [['z22+!', 'm123', 'p555', 's789', 'z111']])

    def test_normal_fulou(self):
        assert (hule_mianzi(Shoupai.from_str('m123p055z1112,s7-89'), 'z2=')
                == [['z22=!', 'm123', 'p555', 'z111', 's7-89']])

    def test_goushi_zimo(self):
        assert (hule_mianzi(Shoupai.from_str('m9p19s19z12345677m1'), None)
                == [['z77', 'm1_!', 'm9', 'p1', 'p9', 's1', 's9', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6']])

    def test_goushi_13men_rong(self):
        assert (hule_mianzi(Shoupai.from_str('m19p19s19z1234567'), 'm9+')
                == [['m99+!', 'm1', 'p1', 'p9', 's1', 's9', 'z1', 'z2', 'z3', 'z4', 'z5', 'z6', 'z7']])

    def test_jiulian(self):
        assert (hule_mianzi(Shoupai.from_str('m1112345678999'), 'm0=')
                == [['m55=!', 'm111', 'm234', 'm678', 'm999'],
                    ['m11123456789995=!']])

    def test_no_hule_shoupai_underflow(self):
        assert hule_mianzi(Shoupai.from_str('m123p055s789z1122')) == []

    def test_no_hule_three_mianzi(self):
        assert hule_mianzi(Shoupai.from_str('___m123p055z2,s7-89'), 'z2=') == []

    def test_no_hule_one_duizi(self):
        assert hule_mianzi(Shoupai.from_str('m22')) == []

    def test_no_hule_goushi_tingpai(self):
        assert hule_mianzi(Shoupai.from_str('m19p19s19z123456'), 'z7=') == []

    def test_no_hule_jiulian_tingpai(self):
        assert hule_mianzi(Shoupai.from_str('m111234567899'), 'm9=') == []

    def test_single_hule(self):
        assert (hule_mianzi(Shoupai.from_str('m111123p789999z1z1'), None)
                == [['z11_!', 'm123', 'm111', 'p789', 'p999']])

    def test_multi_hule_erbeiko_or_qidui(self):
        assert (hule_mianzi(Shoupai.from_str('m223344p556677s88'))
                == [['s88_!', 'm234', 'm234', 'p567', 'p567'],
                    ['m22', 'm33', 'm44', 'p55', 'p66', 'p77', 's88_!']])

    def test_multi_hule_shunzi_or_kezi(self):
        assert (hule_mianzi(Shoupai.from_str('m111222333p89997'))
                == [['p99', 'm123', 'm123', 'm123', 'p7_!89'],
                    ['p99', 'm111', 'm222', 'm333', 'p7_!89']])

    def test_multi_hule_pinghu_or_sansetongshun(self):
        assert (hule_mianzi(Shoupai.from_str('m2234455p234s234m3'))
                == [['m22', 'm3_!45', 'm345', 'p234', 's234'],
                    ['m55', 'm23_!4', 'm234', 'p234', 's234']])

    def test_multi_hule_include_ankezi(self):
        assert (hule_mianzi(Shoupai.from_str('m23p567s33345666m1'))
                == [['s33', 'm1_!23', 'p567', 's345', 's666'],
                    ['s66', 'm1_!23', 'p567', 's333', 's456']])

    def test_multi_hule_jiulian(self):
        assert (hule_mianzi(Shoupai.from_str('s1113445678999s2'))
                == [['s99', 's111', 's2_!34', 's456', 's789'],
                    ['s11134456789992_!']])

    def test_bug_anganged_5th_pai(self):
        assert (hule_mianzi(Shoupai.from_str('s4067999z444s8,s8888'))
                == [['s99', 's456', 's78_!9', 'z444', 's8888']])
