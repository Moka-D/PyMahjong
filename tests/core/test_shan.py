import pytest

from jongpy.core.shan import Shan
from jongpy.core.rule import rule
from jongpy.core.exceptions import PaiFormatError, InvalidOperationError


def _shan(rule_={}):
    return Shan(rule(rule_))


class TestShanZhenbaopai:

    def test_m1_to_m2(self):
        assert Shan.zhenbaopai('m1') == 'm2'

    def test_m9_to_m1(self):
        assert Shan.zhenbaopai('m9') == 'm1'

    def test_m0_to_m6(self):
        assert Shan.zhenbaopai('m0') == 'm6'

    def test_p1_to_p2(self):
        assert Shan.zhenbaopai('p1') == 'p2'

    def test_p9_to_p1(self):
        assert Shan.zhenbaopai('p9') == 'p1'

    def test_p0_to_p6(self):
        assert Shan.zhenbaopai('p0') == 'p6'

    def test_s1_to_s2(self):
        assert Shan.zhenbaopai('s1') == 's2'

    def test_s9_to_s1(self):
        assert Shan.zhenbaopai('s9') == 's1'

    def test_s0_to_s6(self):
        assert Shan.zhenbaopai('s0') == 's6'

    def test_z1_to_z2(self):
        assert Shan.zhenbaopai('z1') == 'z2'

    def test_z4_to_z1(self):
        assert Shan.zhenbaopai('z4') == 'z1'

    def test_z5_to_z6(self):
        assert Shan.zhenbaopai('z5') == 'z6'

    def test_z7_to_z5(self):
        assert Shan.zhenbaopai('z7') == 'z5'

    def test_error_invalid_pai(self):
        with pytest.raises(PaiFormatError):
            Shan.zhenbaopai('z0')


class TestShanInit:

    def test_exist_class(self):
        assert Shan(rule())

    def test_without_hongpai(self):
        pai = ('m1,m1,m1,m1,m2,m2,m2,m2,m3,m3,m3,m3,m4,m4,m4,m4,m5,m5,m5,m5,'
               + 'm6,m6,m6,m6,m7,m7,m7,m7,m8,m8,m8,m8,m9,m9,m9,m9,'
               + 'p1,p1,p1,p1,p2,p2,p2,p2,p3,p3,p3,p3,p4,p4,p4,p4,p5,p5,p5,p5,'
               + 'p6,p6,p6,p6,p7,p7,p7,p7,p8,p8,p8,p8,p9,p9,p9,p9,'
               + 's1,s1,s1,s1,s2,s2,s2,s2,s3,s3,s3,s3,s4,s4,s4,s4,s5,s5,s5,s5,'
               + 's6,s6,s6,s6,s7,s7,s7,s7,s8,s8,s8,s8,s9,s9,s9,s9,'
               + 'z1,z1,z1,z1,z2,z2,z2,z2,z3,z3,z3,z3,z4,z4,z4,z4,'
               + 'z5,z5,z5,z5,z6,z6,z6,z6,z7,z7,z7,z7')
        assert ",".join(sorted(list(Shan({'hongpai': {'m': 0, 'p': 0, 's': 0}})._pai))) == pai

    def test_with_hongpai(self):
        pai = ('m0,m1,m1,m1,m1,m2,m2,m2,m2,m3,m3,m3,m3,m4,m4,m4,m4,m5,m5,m5,'
               + 'm6,m6,m6,m6,m7,m7,m7,m7,m8,m8,m8,m8,m9,m9,m9,m9,'
               + 'p0,p0,p1,p1,p1,p1,p2,p2,p2,p2,p3,p3,p3,p3,p4,p4,p4,p4,p5,p5,'
               + 'p6,p6,p6,p6,p7,p7,p7,p7,p8,p8,p8,p8,p9,p9,p9,p9,'
               + 's0,s0,s0,s1,s1,s1,s1,s2,s2,s2,s2,s3,s3,s3,s3,s4,s4,s4,s4,s5,'
               + 's6,s6,s6,s6,s7,s7,s7,s7,s8,s8,s8,s8,s9,s9,s9,s9,'
               + 'z1,z1,z1,z1,z2,z2,z2,z2,z3,z3,z3,z3,z4,z4,z4,z4,'
               + 'z5,z5,z5,z5,z6,z6,z6,z6,z7,z7,z7,z7')
        assert ",".join(sorted(list(Shan({'hongpai': {'m': 1, 'p': 2, 's': 3}})._pai))) == pai


class TestShanPaishu:

    def test_paishu(self):
        assert _shan().paishu == 122


class TestShanBaopai:

    def test_baopai_len(self):
        assert len(_shan().baopai) == 1


class TestShanFubaopai:

    def test_init_none(self):
        assert _shan().fubaopai is None

    def test_after_closed(self):
        assert len(_shan().close().fubaopai) == 1

    def test_rule_nofubaopai(self):
        assert _shan({'fubaopai': False}).close().fubaopai is None


class TestShanZimo:

    def test_after_init(self):
        assert _shan().zimo()

    def test_paishu_after_zimo(self):
        shan = _shan()
        assert shan.paishu - 1 == (shan.zimo() and shan.paishu)

    def test_error_wangpai(self):
        shan = _shan()
        while shan.paishu:
            shan.zimo()
        with pytest.raises(InvalidOperationError):
            shan.zimo()

    def test_error_after_closed(self):
        with pytest.raises(InvalidOperationError):
            _shan().close().zimo()


class TestShanGangzimo:

    def test_after_init(self):
        assert _shan().gangzimo()

    def test_paishu_after_gangzimo(self):
        shan = _shan()
        assert shan.paishu - 1 == (shan.gangzimo() and shan.paishu)

    def test_error_zimo_after_gangzimo(self):
        shan = _shan()
        with pytest.raises(InvalidOperationError):
            shan.gangzimo() and shan.zimo()

    def test_error_gangzimo_after_gangzimo(self):
        shan = _shan()
        with pytest.raises(InvalidOperationError):
            shan.gangzimo() and shan.gangzimo()

    def test_error_haidi(self):
        shan = _shan()
        while shan.paishu:
            shan.zimo()
        with pytest.raises(InvalidOperationError):
            shan.gangzimo()

    def test_error_after_closed(self):
        with pytest.raises(InvalidOperationError):
            _shan().close().gangzimo()

    def test_error_5th(self):
        shan = _shan()
        for _ in range(0, 4):
            shan.gangzimo()
            shan.kaigang()
        with pytest.raises(InvalidOperationError):
            shan.gangzimo()

    def test_error_5th_no_gangbaopai(self):
        shan = _shan({'gang_baopai': False})
        for _ in range(0, 4):
            shan.gangzimo()
        assert len(shan.baopai) == 1
        with pytest.raises(InvalidOperationError):
            shan.gangzimo()


class TestShanKaigang:

    def test_error_after_init(self):
        with pytest.raises(InvalidOperationError):
            _shan().kaigang()

    def test_after_gangzimo(self):
        shan = _shan()
        assert shan.gangzimo() and shan.kaigang()

    def test_baopai(self):
        shan = _shan()
        shan.gangzimo()
        assert len(shan.baopai) + 1 == len(shan.kaigang().baopai)

    def test_fubaopai(self):
        shan = _shan()
        shan.gangzimo()
        assert len(shan.kaigang().close().fubaopai) == 2

    def test_zimo(self):
        shan = _shan()
        shan.gangzimo()
        assert shan.kaigang().zimo()

    def test_gangzimo(self):
        shan = _shan()
        shan.gangzimo()
        assert shan.kaigang().gangzimo()

    def test_error_after_closed(self):
        shan = _shan()
        shan.gangzimo()
        with pytest.raises(InvalidOperationError):
            shan.close().kaigang()

    def test_error_no_gangbaopai(self):
        shan = _shan({'gang_baopai': False})
        shan.gangzimo()
        with pytest.raises(InvalidOperationError):
            shan.kaigang()

    def test_rule_no_gangfubaopai(self):
        shan = _shan({'gang_fubaopai': False})
        shan.gangzimo()
        assert len(shan.kaigang().close().fubaopai) == 1

    def test_rule_no_fubaopai(self):
        shan = _shan({'fubaopai': False})
        shan.gangzimo()
        assert shan.kaigang().close().fubaopai is None
