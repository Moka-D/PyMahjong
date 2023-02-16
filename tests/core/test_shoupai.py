import pytest
import copy

from jongpy.core.shoupai import Shoupai
from jongpy.core.exceptions import (PaiFormatError,
                                    PaiOverFlowError,
                                    PaiNotExistError,
                                    ShoupaiOverFlowError,
                                    ShoupaiUnderFlowError,
                                    MianziFormatError,
                                    InvalidOperationError)


def _shoupai(paistr: str):
    return Shoupai.from_str(paistr)


class TestShoupaiValidPai:

    def test_normal(self):
        assert 'm1' == Shoupai.valid_pai('m1')

    def test_normal_discarding_zimo(self):
        assert 'p2_' == Shoupai.valid_pai('p2_')

    def test_normal_lizhi(self):
        assert 's3*' == Shoupai.valid_pai('s3*')

    def test_normal_discarding_zimo_lizhi(self):
        assert 'z4_*' == Shoupai.valid_pai('z4_*')

    def test_normal_fulou(self):
        assert 'm0-' == Shoupai.valid_pai('m0-')

    def test_normal_discarding_zimo_fulou(self):
        assert 'p5_+' == Shoupai.valid_pai('p5_+')

    def test_normal_lizhi_fulou(self):
        assert 's6*=' == Shoupai.valid_pai('s6*=')

    def test_normal_discarding_zimo_lizhi_fulou(self):
        assert 'z7_*-' == Shoupai.valid_pai('z7_*-')

    def test_error_hidden(self):
        assert Shoupai.valid_pai('_') is None

    def test_error1(self):
        assert Shoupai.valid_pai('x') is None

    def test_error2(self):
        assert Shoupai.valid_pai('mm') is None

    def test_error3(self):
        assert Shoupai.valid_pai('z0') is None

    def test_error4(self):
        assert Shoupai.valid_pai('z8') is None

    def test_error5(self):
        assert Shoupai.valid_pai('m9x') is None

    def test_error6(self):
        assert Shoupai.valid_pai('m9=*') is None

    def test_error7(self):
        assert Shoupai.valid_pai('m9*_') is None

    def test_error8(self):
        assert Shoupai.valid_pai('m9=_') is None


class TestShoupaiValidMianzi:

    def test_normal_kezi1(self):
        assert Shoupai.valid_mianzi('m111+') == 'm111+'

    def test_normal_kezi2(self):
        assert Shoupai.valid_mianzi('p555=') == 'p555='

    def test_normal_kezi3(self):
        assert Shoupai.valid_mianzi('s999-') == 's999-'

    def test_normal_kezi_hongpai1(self):
        assert Shoupai.valid_mianzi('p550=') == 'p550='

    def test_normal_kezi_hongpai2(self):
        assert Shoupai.valid_mianzi('p055=') == 'p505='

    def test_normal_gang1(self):
        assert Shoupai.valid_mianzi('z777+7') == 'z777+7'

    def test_normal_gang2(self):
        assert Shoupai.valid_mianzi('m2222') == 'm2222'

    def test_normal_gang_hongpai1(self):
        assert Shoupai.valid_mianzi('p5550=') == 'p5550='

    def test_normal_gang_hongpai2(self):
        assert Shoupai.valid_mianzi('p055=0') == 'p505=0'

    def test_normal_gang_hongpai3(self):
        assert Shoupai.valid_mianzi('p000=0') == 'p000=0'

    def test_normal_gang_hongpai4(self):
        assert Shoupai.valid_mianzi('s0555-') == 's5505-'

    def test_normal_gang_hongpai5(self):
        assert Shoupai.valid_mianzi('s0055-') == 's5005-'

    def test_normal_gang_hongpai6(self):
        assert Shoupai.valid_mianzi('s0005') == 's5000'

    def test_normal_gang_hongpai7(self):
        assert Shoupai.valid_mianzi('s0000') == 's0000'

    def test_normal_shunzi1(self):
        assert Shoupai.valid_mianzi('m1-23') == 'm1-23'

    def test_normal_shunzi2(self):
        assert Shoupai.valid_mianzi('m12-3') == 'm12-3'

    def test_normal_shunzi3(self):
        assert Shoupai.valid_mianzi('m123-') == 'm123-'

    def test_normal_shunzi4(self):
        assert Shoupai.valid_mianzi('m231-') == 'm1-23'

    def test_normal_shunzi5(self):
        assert Shoupai.valid_mianzi('m312-') == 'm12-3'

    def test_normal_shunzi6(self):
        assert Shoupai.valid_mianzi('m3-12') == 'm123-'

    def test_normal_shunzi_hongpai(self):
        assert Shoupai.valid_mianzi('m460-') == 'm40-6'

    def test_error1(self):
        assert Shoupai.valid_mianzi('m1234-') is None

    def test_error2(self):
        assert Shoupai.valid_mianzi('m135-') is None

    def test_error3(self):
        assert Shoupai.valid_mianzi('m1234') is None

    def test_error4(self):
        assert Shoupai.valid_mianzi('m123') is None

    def test_error5(self):
        assert Shoupai.valid_mianzi('m111') is None

    def test_error6(self):
        assert Shoupai.valid_mianzi('z111=0') is None


class TestShoupaiConstructor:

    def test_make_instance(self):
        assert Shoupai()

    def test_by_qipai(self):
        qipai = ['m0', 'm1', 'm9', 'p0', 'p1', 'p9', 's0', 's1', 's9', 'z1', 'z2', 'z6', 'z7']
        assert Shoupai(qipai)

    def test_hidden_pai(self):
        assert Shoupai(['_'])

    def test_error_invalid_qipai(self):
        with pytest.raises(PaiFormatError):
            Shoupai(['z0'])

    def test_error_pai_overflow(self):
        with pytest.raises(PaiOverFlowError):
            Shoupai(['m1', 'm1', 'm1', 'm1', 'm1'])


class TestShoupaiFromString:

    def test_without_parameter(self):
        assert str(Shoupai.from_str()) == ''

    def test_empty_str(self):
        assert str(Shoupai.from_str('')) == ''

    def test_without_fulou(self):
        assert str(Shoupai.from_str('z7654s987p654m321')) == 'm123p456s789z4567'

    def test_with_fulou(self):
        assert str(Shoupai.from_str('m1,p123-,s555=,z777+7,m9999')) == 'm1,p123-,s555=,z777+7,m9999'

    def test_with_hidden(self):
        assert str(Shoupai.from_str('m123p456____,s789-')) == '____m123p456,s789-'

    def test_underflow(self):
        assert str(Shoupai.from_str('m111p222s333')) == 'm111p222s333'

    def test_overflow(self):
        assert str(Shoupai.from_str('m123456789p123456')) == 'm123456789p1234p5'

    def test_overflow_with_fulou(self):
        assert str(Shoupai.from_str('m123456789p123,z111=')) == 'm123456789p1p2,z111='
        assert str(Shoupai.from_str('m123,z111=,p123-,s555=,z777+')) == 'm1m2,z111=,p123-,s555=,z777+'

    def test_zimo(self):
        assert str(Shoupai.from_str('m11123456789991')) == 'm1112345678999m1'

    def test_zimo_hongpai(self):
        assert str(Shoupai.from_str('m11123456789990')) == 'm1112345678999m0'

    def test_zimo_with_fulou(self):
        assert str(Shoupai.from_str('m12p345s678z23m3,z111=')) == 'm12p345s678z23m3,z111='

    def test_shoupai_hongpai(self):
        assert str(Shoupai.from_str('m5550p5500s0000z00')) == 'm0555p0055s0000'

    def test_lizhi(self):
        assert str(Shoupai.from_str('m123p456s789z1112*')) == 'm123p456s789z1112*'

    def test_lizhi_angang(self):
        assert str(Shoupai.from_str('m123p456s789z2*,z1111')) == 'm123p456s789z2*,z1111'

    def test_lizhi_fulou(self):
        assert str(Shoupai.from_str('m123p456s789z2*,z111+')) == 'm123p456s789z2*,z111+'

    def test_normalize_chi(self):
        assert str(Shoupai.from_str('m123p456s789z2,m403-')) == 'm123p456s789z2,m3-40'
        assert str(Shoupai.from_str('m123p456s789z2,m304-')) == 'm123p456s789z2,m34-0'
        assert str(Shoupai.from_str('m123p456s789z2,m345-')) == 'm123p456s789z2,m345-'

    def test_normalize_peng(self):
        assert str(Shoupai.from_str('m123p456s789z2,p050+')) == 'm123p456s789z2,p500+'
        assert str(Shoupai.from_str('m123p456s789z2,p055+')) == 'm123p456s789z2,p505+'
        assert str(Shoupai.from_str('m123p456s789z2,p550+')) == 'm123p456s789z2,p550+'

    def test_normalize_gang(self):
        assert str(Shoupai.from_str('m123p456s789z2,s0555=')) == 'm123p456s789z2,s5505='
        assert str(Shoupai.from_str('m123p456s789z2,s0050=')) == 'm123p456s789z2,s5000='
        assert str(Shoupai.from_str('m123p456s789z2,s0505')) == 'm123p456s789z2,s5500'

    def test_ignore_invalid_fulou(self):
        assert str(Shoupai.from_str('m123p456s789z2,z000+')) == 'm123p456s789z2'
        assert str(Shoupai.from_str('m123p456s789z2,z888+')) == 'm123p456s789z2'

    def test_ignore_zipai_chi(self):
        assert str(Shoupai.from_str('m123p456s789z2,z1-23')) == 'm123p456s789z2'

    def test_ignore_shimacha_chi(self):
        assert str(Shoupai.from_str('m123p456s789z2,s1+23')) == 'm123p456s789z2'

    def test_ignore_duizi_fulou(self):
        assert str(Shoupai.from_str('m123p456s789z2,z11-')) == 'm123p456s789z2'

    def test_ignore_ryankan_fulou(self):
        assert str(Shoupai.from_str('m123p456s789z2,s13-5')) == 'm123p456s789z2'

    def test_ignore_renko_fulou(self):
        assert str(Shoupai.from_str('m123p456s789z2,m1p2s3-')) == 'm123p456s789z2'

    def test_after_fulou(self):
        assert str(Shoupai.from_str('p456s789z1,m12-3,p999=,')) == 'p456s789z1,m12-3,p999=,'


class TestShoupaiCopy:

    def test_copy(self):
        shoupai = Shoupai()
        assert shoupai != copy.copy(shoupai)

    def test_copy_shoupai(self):
        shoupai = Shoupai.from_str('m123p456s789z4567')
        assert str(shoupai) == str(copy.copy(shoupai))

    def test_copy_fulou(self):
        shoupai = Shoupai.from_str('m1,p123-,s555=,z777+7,m9999')
        assert str(shoupai) == str(copy.copy(shoupai))

    def test_copy_zimo(self):
        shoupai = Shoupai.from_str('m11123456789991')
        assert str(shoupai) == str(copy.copy(shoupai))

    def test_copy_lizhi(self):
        shoupai = Shoupai.from_str('m123p456s789z1112*')
        assert str(shoupai) == str(copy.copy(shoupai))

    def test_copy_hidden(self):
        shoupai = Shoupai.from_str('___________,m123-')
        assert str(shoupai) == str(copy.copy(shoupai))

    def test_not_share_zimo(self):
        shoupai = Shoupai.from_str('m123p456s789z4567')
        copied = copy.copy(shoupai)
        copied.zimo('m1')
        assert str(shoupai) != str(copied)

    def test_not_share_dapai(self):
        shoupai = Shoupai.from_str('m123p456s789z34567')
        copied = copy.copy(shoupai)
        copied.dapai('m1')
        assert str(shoupai) != str(copied)

    def test_not_share_fulou(self):
        shoupai = Shoupai.from_str('m123p456s789z1167')
        copied = copy.copy(shoupai)
        copied.fulou('z111=')
        assert str(shoupai) != str(copied)

    def test_not_share_gang(self):
        shoupai = Shoupai.from_str('m123p456s789z11112')
        copied = copy.copy(shoupai)
        copied.gang('z1111')
        assert str(shoupai) != str(copied)

    def test_not_share_lizhi(self):
        shoupai = Shoupai.from_str('m123p456s789z11223')
        copied = copy.copy(shoupai)
        copied.dapai('z3*')
        assert str(shoupai) != str(copied)


class TestShoupaiUpdate:

    @pytest.fixture
    def setup(self):
        self.shoupai = Shoupai()

    def test_update(self, setup):
        assert str(self.shoupai.update('m123p456s789z1122z2')) == 'm123p456s789z1122z2'

    def test_update_fulou(self, setup):
        assert str(self.shoupai.update('m123p456s789z2,z111=')) == 'm123p456s789z2,z111='

    def test_update_lizhi(self, setup):
        assert str(self.shoupai.update('m123p456s789z1122*')) == 'm123p456s789z1122*'

    def test_update_hidden(self, setup):
        assert str(self.shoupai.update('__________,z111=')) == '__________,z111='


class TestShoupaiZimo:

    @pytest.fixture
    def setup(self):
        self.shoupai = _shoupai('m123p456s789z4567')

    def test_manzu(self, setup):
        assert str(self.shoupai.zimo('m1')) == 'm123p456s789z4567m1'

    def test_pinzu(self, setup):
        assert str(self.shoupai.zimo('p1')) == 'm123p456s789z4567p1'

    def test_sohzu(self, setup):
        assert str(self.shoupai.zimo('s1')) == 'm123p456s789z4567s1'

    def test_zipai(self, setup):
        assert str(self.shoupai.zimo('z1')) == 'm123p456s789z4567z1'

    def test_hongpai(self, setup):
        assert str(self.shoupai.zimo('m0')) == 'm123p456s789z4567m0'

    def test_hidden(self, setup):
        assert str(self.shoupai.zimo('_')) == 'm123p456s789z4567_'

    def test_error_invalid_pai(self, setup):
        with pytest.raises(PaiFormatError):
            self.shoupai.zimo('')
        with pytest.raises(PaiFormatError):
            self.shoupai.zimo('z0')
        with pytest.raises(PaiFormatError):
            self.shoupai.zimo('z8')
        with pytest.raises(PaiFormatError):
            self.shoupai.zimo('mm')
        with pytest.raises(PaiFormatError):
            self.shoupai.zimo('xx')

    def test_error_double_zimo(self):
        with pytest.raises(ShoupaiOverFlowError):
            _shoupai('m123p456s789z34567').zimo('m1')

    def test_error_after_fulou(self):
        with pytest.raises(ShoupaiOverFlowError):
            _shoupai('m123p456z34567,s789-,').zimo('m1')

    def test_nocheck_shoupai_overflow(self):
        assert str(_shoupai('m123p456s789z34567').zimo('m1', False)) == 'm123p456s789z34567m1'

    def test_error_pai_overflow(self):
        with pytest.raises(PaiOverFlowError):
            _shoupai('m123p456s789z1111').zimo('z1')
        with pytest.raises(PaiOverFlowError):
            _shoupai('m455556s789z1111').zimo('m0')


class TestShoupaiDapai:

    @pytest.fixture
    def setup(self):
        self.shoupai = _shoupai('m123p456s789z34567')

    def test_manzu(self, setup):
        assert str(self.shoupai.dapai('m1')) == 'm23p456s789z34567'

    def test_pinzu(self, setup):
        assert str(self.shoupai.dapai('p4')) == 'm123p56s789z34567'

    def test_sohzu(self, setup):
        assert str(self.shoupai.dapai('s7')) == 'm123p456s89z34567'

    def test_zipai(self, setup):
        assert str(self.shoupai.dapai('z3')) == 'm123p456s789z4567'

    def test_hongpai(self):
        assert str(_shoupai('m123p406s789z34567').dapai('p0')) == 'm123p46s789z34567'

    def test_lizhi(self, setup):
        assert str(self.shoupai.dapai('z7*')) == 'm123p456s789z3456*'

    def test_nocheck_after_lizhi(self):
        assert str(_shoupai('m123p456s789z11223*').dapai('z1')) == 'm123p456s789z1223*'

    def test_hidden(self):
        assert str(_shoupai('______________').dapai('m1')) == '_____________'

    def test_error_invalid_pai(self, setup):
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('')
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('z0')
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('z8')
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('mm')
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('xx')

    def test_error_hidden(self, setup):
        with pytest.raises(PaiFormatError):
            self.shoupai.dapai('_')

    def test_error_after_dapai(self):
        with pytest.raises(ShoupaiUnderFlowError):
            _shoupai('m123p456s789z4567').dapai('m1')

    def test_nocheck_underflow(self):
        assert str(_shoupai('m123p456s789z4567').dapai('m1', False)) == 'm23p456s789z4567'

    def test_error_noexist_pai(self, setup):
        with pytest.raises(PaiNotExistError):
            self.shoupai.dapai('z1')
        with pytest.raises(PaiNotExistError):
            self.shoupai.dapai('p0')
        with pytest.raises(PaiNotExistError):
            _shoupai('m123p406s789z34567').dapai('p5')


class TestShoupaiFulou:

    def test_manzu(self):
        assert str(_shoupai('m23p456s789z34567').fulou('m1-23')) == 'p456s789z34567,m1-23,'

    def test_pinzu(self):
        assert str(_shoupai('m123p46s789z34567').fulou('p45-6')) == 'm123s789z34567,p45-6,'

    def test_sohzu(self):
        assert str(_shoupai('m123p456s99z34567').fulou('s999+')) == 'm123p456z34567,s999+,'

    def test_zipai(self):
        assert str(_shoupai('m123p456s789z1167').fulou('z111=')) == 'm123p456s789z67,z111=,'

    def test_hongpai(self):
        assert str(_shoupai('m123p500s789z4567').fulou('p5005-')) == 'm123s789z4567,p5005-'

    def test_lizhi(self):
        assert str(_shoupai('m123p456s789z4567*').fulou('m1-23')) == 'm1p456s789z4567*,m1-23,'

    def test_hidden(self):
        assert str(_shoupai('_____________').fulou('m1-23')) == '___________,m1-23,'

    def test_error_invalid_mianzi(self):
        shoupai = _shoupai('m123p456s789z4567')
        with pytest.raises(MianziFormatError):
            shoupai.fulou('z3-45')
        with pytest.raises(MianziFormatError):
            shoupai.fulou('m231-')

    def test_error_angang(self):
        with pytest.raises(InvalidOperationError):
            _shoupai('_____________').fulou('m1111')

    def test_error_gagan(self):
        with pytest.raises(InvalidOperationError):
            _shoupai('_____________').fulou('m111+1')

    def test_error_after_zimo(self):
        with pytest.raises(ShoupaiOverFlowError):
            _shoupai('m123p456s789z11567').fulou('z111=')

    def test_error_after_fulou(self):
        with pytest.raises(ShoupaiOverFlowError):
            _shoupai('m123p456s789z22,z111=,').fulou('z222=')

    def test_nocheck_tapai(self):
        assert str(_shoupai('m123p456s789z11567').fulou('z111=', False)) == 'm123p456s789z567,z111=,'
        assert str(_shoupai('m123p456s789z22,z111=,').fulou('z222=', False)) == 'm123p456s789,z111=,z222=,'

    def test_error_noexist_pai(self):
        with pytest.raises(PaiNotExistError):
            _shoupai('m123p456s789z2,z111=').fulou('z333=')
        with pytest.raises(PaiNotExistError):
            _shoupai('m123p40s789z22,z111=').fulou('p456-')
        with pytest.raises(PaiNotExistError):
            _shoupai('m123p45s789z22,z111=').fulou('p406-')


class TestShoupaiGang:

    def test_manzu_angang(self):
        assert str(_shoupai('m1111p456s789z4567').gang('m1111')) == 'p456s789z4567,m1111'

    def test_manzu_gagang(self):
        assert str(_shoupai('m1p456s789z4567,m111+').gang('m111+1')) == 'p456s789z4567,m111+1'

    def test_pinzu_angang(self):
        assert str(_shoupai('m123p5555s789z4567').gang('p5555')) == 'm123s789z4567,p5555'

    def test_pinzu_gagang(self):
        assert str(_shoupai('m123p5s789z4567,p555=').gang('p555=5')) == 'm123s789z4567,p555=5'

    def test_sohzu_angang(self):
        assert str(_shoupai('m123p456s9999z4567').gang('s9999')) == 'm123p456z4567,s9999'

    def test_sohzu_gagan(self):
        assert str(_shoupai('m123p456s9z4567,s999-').gang('s999-9')) == 'm123p456z4567,s999-9'

    def test_zipai_angang(self):
        assert str(_shoupai('m123p456s789z67777').gang('z7777')) == 'm123p456s789z6,z7777'

    def test_zipai_gagan(self):
        assert str(_shoupai('m123p456s789z67,z777+').gang('z777+7')) == 'm123p456s789z6,z777+7'

    def test_hongpai_angang(self):
        assert str(_shoupai('m0055p456s789z4567').gang('m5500')) == 'p456s789z4567,m5500'

    def test_hongpai_gagan(self):
        assert str(_shoupai('m123p5s789z4567,p505=').gang('p505=5')) == 'm123s789z4567,p505=5'

    def test_nocheck_lizhi_angang(self):
        assert str(_shoupai('m1111p456s789z4567*').gang('m1111')) == 'p456s789z4567*,m1111'

    def test_nocheck_lizhi_gagang(self):
        assert str(_shoupai('m1p456s789z4567*,m111+').gang('m111+1')) == 'p456s789z4567*,m111+1'

    def test_hidden_angang(self):
        assert str(_shoupai('______________').gang('m5550')) == '__________,m5550'

    def test_hidden_gagang(self):
        assert str(_shoupai('___________,m555=').gang('m555=0')) == '__________,m555=0'

    def test_error_shunzi(self):
        with pytest.raises(InvalidOperationError):
            _shoupai('m1112456s789z4567').gang('m456-')

    def test_error_kezi(self):
        with pytest.raises(InvalidOperationError):
            _shoupai('m1112456s789z4567').gang('m111+')

    def test_error_invalid_angang(self):
        with pytest.raises(MianziFormatError):
            _shoupai('m1112456s789z4567').gang('m1112')

    def test_error_invalid_gagang(self):
        with pytest.raises(MianziFormatError):
            _shoupai('m2456s789z4567,m111+').gang('m111+2')

    def test_error_after_dapai(self):
        with pytest.raises(ShoupaiUnderFlowError):
            _shoupai('m1111p456s789z456').gang('m1111')

    def test_error_after_fulou(self):
        with pytest.raises(ShoupaiUnderFlowError):
            _shoupai('m1111s789z4567,p456-,').gang('m1111')

    def test_error_after_gang(self):
        shoupai = _shoupai('m1111p4444s789z567').gang('m1111')
        with pytest.raises(ShoupaiUnderFlowError):
            shoupai.gang('p4444')

    def test_nocheck_underflow(self):
        assert str(_shoupai('m1111p456s789z567').gang('m1111', False)) == 'p456s789z567,m1111'
        assert str(_shoupai('m1111s789z4567,p456-,').gang('m1111', False)) == 's789z4567,p456-,m1111'
        assert str(_shoupai('m1111p4444s789z567').gang('m1111', False).gang('p4444', False)) == 's789z567,m1111,p4444'

    def test_error_noexist_angang(self):
        with pytest.raises(PaiNotExistError):
            _shoupai('m1112p456s789z4567').gang('m1111')

    def test_error_noexist_gagang(self):
        with pytest.raises(PaiNotExistError):
            _shoupai('m13p456s789z567,m222=').gang('m2222')
        with pytest.raises(PaiNotExistError):
            _shoupai('m10p456s789z567,m555=').gang('m555=5')
        with pytest.raises(PaiNotExistError):
            _shoupai('m15p456s789z567,m555=').gang('m555=0')

    def test_error_noexsit_minko_gagan(self):
        with pytest.raises(InvalidOperationError):
            _shoupai('m12p456s789z5657,m222=').gang('m111=1')


class TestShoupaiMenqian:

    def test_noexist_fulou(self):
        assert _shoupai('m123p0s789z4567').menqian

    def test_exist_fulou(self):
        assert not _shoupai('p0s789z4567,m123-').menqian

    def test_angang(self):
        assert _shoupai('m123p0s789,z1111').menqian


class TestShoupaiLizhi:

    def test_ng_lizhi(self):
        assert not _shoupai('_____________').lizhi

    def test_ok_lizhi(self):
        assert _shoupai('_____________').zimo('z7').dapai('z7_*').lizhi


class TestShoupaiGetDapai:

    def test_ng_after_zimo(self):
        assert _shoupai('m123p406s789z4567').get_dapai() is None
        assert _shoupai('_____________').get_dapai() is None

    def test_ng_after_fulou(self):
        assert _shoupai('m123p406s789z2,z111+').get_dapai() is None
        assert _shoupai('__________,z111+').get_dapai() is None

    def test_ok_menqian_after_zimo(self):
        assert (_shoupai('m123p406s789z11123').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p0', 'p6', 's7', 's8', 's9', 'z1', 'z2', 'z3_'])

    def test_ok_fulou_after_zimo(self):
        assert (_shoupai('m123p406s789z12,z111+').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p0', 'p6', 's7', 's8', 's9', 'z1', 'z2_'])

    def test_after_lizhi(self):
        assert _shoupai('m123p456s789z1234m1*').get_dapai() == ['m1_']

    def test_hongpai(self):
        assert (_shoupai('m123p405s789z11123').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p0', 'p5', 's7', 's8', 's9',
                    'z1', 'z2', 'z3_'])
        assert (_shoupai('m123p45s789z11123p0').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p5', 's7', 's8', 's9', 'z1', 'z2', 'z3', 'p0_'])

    def test_abandon_zimo(self):
        assert (_shoupai('m123p45s789z11123p5').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p5', 's7', 's8', 's9',
                    'z1', 'z2', 'z3', 'p5_'])
        assert (_shoupai('m123p405s789z1112p0').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p0', 'p5', 's7', 's8', 's9', 'z1', 'z2', 'p0_'])

    def test_hidden(self):
        assert _shoupai('______________').get_dapai() == []
        assert _shoupai('___________,m123-,').get_dapai() == []

    def test_kuikae_ryanmen(self):
        assert (_shoupai('m145p406s789z23,m1-23,').get_dapai()
                == ['m5', 'p4', 'p0', 'p6', 's7', 's8', 's9', 'z2', 'z3'])
        assert (_shoupai('m145p406s789z23,m234-,').get_dapai()
                == ['m5', 'p4', 'p0', 'p6', 's7', 's8', 's9', 'z2', 'z3'])

    def test_kuikae_kanchan(self):
        assert (_shoupai('m123p258s789z23,p45-6,').get_dapai()
                == ['m1', 'm2', 'm3', 'p2', 'p8', 's7', 's8', 's9', 'z2', 'z3'])

    def test_kuikae_penchan(self):
        assert (_shoupai('m123p456s467z23,s7-89,').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p5', 'p6', 's4', 's6', 'z2', 'z3'])

    def test_kuikae_peng(self):
        assert (_shoupai('m123p456s789z12,z111+,').get_dapai()
                == ['m1', 'm2', 'm3', 'p4', 'p5', 'p6', 's7', 's8', 's9', 'z2'])

    def test_kuikae_hongpai_fulou(self):
        assert (_shoupai('m256p456s789z12,m340-,').get_dapai()
                == ['m6', 'p4', 'p5', 'p6', 's7', 's8', 's9', 'z1', 'z2'])

    def test_kuikae_hongpai_dapai(self):
        assert (_shoupai('m206p456s789z12,m345-,').get_dapai()
                == ['m6', 'p4', 'p5', 'p6', 's7', 's8', 's9', 'z1', 'z2'])

    def test_kuikae_hongpai_peng(self):
        assert (_shoupai('m25p1s12678,z666+,m550-,').get_dapai()
                == ['m2', 'p1', 's1', 's2', 's6', 's7', 's8'])

    def test_kuikae_cannot_dapai(self):
        assert _shoupai('m14,p456-,s789-,z111+,m234-,').get_dapai() == []
        assert _shoupai('m14,p456-,s789-,z111+,m1-23,').get_dapai() == []
        assert _shoupai('m22,p456-,s789-,z111+,m12-3,').get_dapai() == []

    def test_allow_kuikae(self):
        assert (_shoupai('m145p406s789z23,m1-23,').get_dapai(False)
                == ['m1', 'm4', 'm5', 'p4', 'p0', 'p6', 's7', 's8', 's9', 'z2', 'z3'])


class TestShoupaiGetChiMianzi:

    def test_ng_after_zimo(self):
        assert _shoupai('m123p456s789z12345').get_chi_mianzi('m1-') is None
        assert _shoupai('______________').get_chi_mianzi('m1-') is None

    def test_ng_after_fulou(self):
        assert _shoupai('m123p456s789z12,z333=,').get_chi_mianzi('m1-') is None

    def test_noexist_chi(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m5-') == []
        assert _shoupai('_____________').get_chi_mianzi('m5-') == []

    def test_exist_one_chi(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m3-') == ['m123-']

    def test_exist_two_chi(self):
        assert _shoupai('m1234p456s789z123').get_chi_mianzi('m3-') == ['m123-', 'm23-4']

    def test_exist_three_chi(self):
        assert _shoupai('m12345p456s789z12').get_chi_mianzi('m3-') == ['m123-', 'm23-4', 'm3-45']

    def test_by_hongpai(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('p0-') == ['p40-6']

    def test_include_hongpai(self):
        assert _shoupai('m123p34067s789z12').get_chi_mianzi('p3-') == ['p3-40']
        assert _shoupai('m123p34067s789z12').get_chi_mianzi('p4-') == ['p34-0', 'p4-06']
        assert _shoupai('m123p34067s789z12').get_chi_mianzi('p6-') == ['p406-', 'p06-7']
        assert _shoupai('m123p34067s789z12').get_chi_mianzi('p7-') == ['p067-']

    def test_without_hongpai(self):
        assert _shoupai('m123p340567s789z1').get_chi_mianzi('p3-') == ['p3-40', 'p3-45']
        assert _shoupai('m123p340567s789z1').get_chi_mianzi('p4-') == ['p34-0', 'p34-5', 'p4-06', 'p4-56']
        assert _shoupai('m123p340567s789z1').get_chi_mianzi('p6-') == ['p406-', 'p456-', 'p06-7', 'p56-7']
        assert _shoupai('m123p340567s789z1').get_chi_mianzi('p7-') == ['p067-', 'p567-']

    def test_abandoned_zimo(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m3_-') == ['m123-']

    def test_lizhied(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m3*-') == ['m123-']

    def test_lizhied_and_abandoned_zimo(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m3_*-') == ['m123-']

    def test_after_lizhi(self):
        assert _shoupai('m123p456s789z1234*').get_chi_mianzi('m3-') == []

    def test_without_kuikae(self):
        assert _shoupai('s6789,m123-,p456-,z111+').get_chi_mianzi('s6-') == []
        assert _shoupai('s6789,m123-,p456-,z111+').get_chi_mianzi('s9-') == []
        assert _shoupai('s7889,m123-,p456-,z111+').get_chi_mianzi('s8-') == []
        assert _shoupai('s7899,m123-,p456-,z111+').get_chi_mianzi('s9-') == []
        assert _shoupai('s7789,m123-,p456-,z111+').get_chi_mianzi('s7-') == []
        assert _shoupai('s6678999,m123-,p456-').get_chi_mianzi('s6-') == []

    def test_nocheck_kuikae(self):
        assert _shoupai('s6789,m123-,p456-,z111+').get_chi_mianzi('s6-', False) == ['s6-78']
        assert _shoupai('s6789,m123-,p456-,z111+').get_chi_mianzi('s9-', False) == ['s789-']
        assert _shoupai('s7889,m123-,p456-,z111+').get_chi_mianzi('s8-', False) == ['s78-9']
        assert _shoupai('s7899,m123-,p456-,z111+').get_chi_mianzi('s9-', False) == ['s789-']
        assert _shoupai('s7789,m123-,p456-,z111+').get_chi_mianzi('s7-', False) == ['s7-89']
        assert _shoupai('s6678999,m123-,p456-').get_chi_mianzi('s6-', False) == ['s6-78']

    def test_error_invalid_pai(self):
        with pytest.raises(PaiFormatError):
            _shoupai('m123p456s789z1234').get_chi_mianzi('mm-')
        with pytest.raises(InvalidOperationError):
            _shoupai('m123p456s789z1234').get_chi_mianzi('m1')

    def test_cannot_zipai(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('z1-') == []

    def test_ng_without_kamicha(self):
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m1+') == []
        assert _shoupai('m123p456s789z1234').get_chi_mianzi('m1=') == []


class TestShoupaiGetPengMianzi:

    def test_ng_after_zimo(self):
        assert _shoupai('m112p456s789z12345').get_peng_mianzi('m1+') is None
        assert _shoupai('______________').get_peng_mianzi('m1-') is None

    def test_ng_after_fulou(self):
        assert _shoupai('m112p456s789z12,z333=,').get_peng_mianzi('m1=') is None

    def test_noexist_peng(self):
        assert _shoupai('m123p456s789z1234').get_peng_mianzi('m1+') == []
        assert _shoupai('_____________').get_peng_mianzi('m1=') == []

    def test_from_shimocha(self):
        assert _shoupai('m112p456s789z1234').get_peng_mianzi('m1+') == ['m111+']

    def test_from_toimen(self):
        assert _shoupai('m123p445s789z1234').get_peng_mianzi('p4=') == ['p444=']

    def test_from_kamicha(self):
        assert _shoupai('m123p345s778z1234').get_peng_mianzi('s7-') == ['s777-']

    def test_by_hongpai(self):
        assert _shoupai('m123p455s789z1234').get_peng_mianzi('p0+') == ['p550+']
        assert _shoupai('m123p405s789z1234').get_peng_mianzi('p0+') == ['p500+']
        assert _shoupai('m123p400s789z1234').get_peng_mianzi('p0+') == ['p000+']

    def test_include_without_hongpai(self):
        assert _shoupai('m123p055s789z1234').get_peng_mianzi('p5=') == ['p505=', 'p555=']
        assert _shoupai('m123p005s789z1234').get_peng_mianzi('p5=') == ['p005=', 'p505=']
        assert _shoupai('m123p000s789z1234').get_peng_mianzi('p5=') == ['p005=']

    def test_abandoned_zimo(self):
        assert _shoupai('m112p456s789z1234').get_peng_mianzi('m1_+') == ['m111+']

    def test_lizhied(self):
        assert _shoupai('m112p456s789z1234').get_peng_mianzi('m1*+') == ['m111+']

    def test_lizhied_and_abandoned_zimo(self):
        assert _shoupai('m112p456s789z1234').get_peng_mianzi('m1_*+') == ['m111+']

    def test_cannot_after_lizhi(self):
        assert _shoupai('m112p456s789z1234*').get_peng_mianzi('m1+') == []

    def test_error_invalid_pai(self):
        with pytest.raises(PaiFormatError):
            assert _shoupai('m112p456s789z1234').get_peng_mianzi('mm+')
        with pytest.raises(InvalidOperationError):
            assert _shoupai('m112p456s789z1234').get_peng_mianzi('m1')


class TestShoupaiGetGangMianzi:

    def test_daimingang_ng_after_zimo(self):
        assert _shoupai('m111p456s789z12345').get_gang_mianzi('m1+') is None
        assert _shoupai('______________').get_gang_mianzi('m1-') is None

    def test_daimingang_ng_after_fulou(self):
        assert _shoupai('m111p456s789z12,z333=,').get_gang_mianzi('m1+') is None

    def test_daimingang_noexist(self):
        assert _shoupai('m123p456s789z1122').get_gang_mianzi('z1+') == []
        assert _shoupai('_____________').get_gang_mianzi('z1=') == []

    def test_daimingang_from_shimocha(self):
        assert _shoupai('m111p456s789z1234').get_gang_mianzi('m1+') == ['m1111+']

    def test_daimingang_from_toimen(self):
        assert _shoupai('m123p444s789z1234').get_gang_mianzi('p4=') == ['p4444=']

    def test_daimingang_from_kamicha(self):
        assert _shoupai('m123p456s777z1234').get_gang_mianzi('s7-') == ['s7777-']

    def test_daimingang_by_hongpai(self):
        assert _shoupai('m123p555s789z1234').get_gang_mianzi('p0+') == ['p5550+']

    def test_daimingang_include_hongpai(self):
        assert _shoupai('m123p055s789z1234').get_gang_mianzi('p5+') == ['p5505+']
        assert _shoupai('m123p005s789z1234').get_gang_mianzi('p5+') == ['p5005+']
        assert _shoupai('m123p000s789z1234').get_gang_mianzi('p5+') == ['p0005+']

    def test_daimingang_abandoned_zimo(self):
        assert _shoupai('m111p456s789z1234').get_gang_mianzi('m1_+') == ['m1111+']

    def test_daimingang_lizhied(self):
        assert _shoupai('m111p456s789z1234').get_gang_mianzi('m1*+') == ['m1111+']

    def test_daimingang_lizhied_and_abandoned_zimo(self):
        assert _shoupai('m111p456s789z1234').get_gang_mianzi('m1_*+') == ['m1111+']

    def test_cannot_after_lizhi(self):
        assert _shoupai('m111p456s789z1234*').get_gang_mianzi('m1+') == []

    def test_error_invalid_pai(self):
        with pytest.raises(PaiFormatError):
            assert _shoupai('m111p555s999z1234').get_gang_mianzi('mm+') == []
        with pytest.raises(InvalidOperationError):
            assert _shoupai('m111p555s999z1234').get_gang_mianzi('m1')

    def test_angang_ng_after_dapai(self):
        assert _shoupai('m1111p555s999z123').get_gang_mianzi() is None
        assert _shoupai('m1111p555s999,z333=').get_gang_mianzi() is None
        assert _shoupai('_____________').get_gang_mianzi() is None

    def test_angang_ng_after_fulou(self):
        assert _shoupai('m11112p555s999,z333=,').get_gang_mianzi() is None

    def test_angang_noexist(self):
        assert _shoupai('m123p456s789z12345').get_gang_mianzi() == []
        assert _shoupai('______________').get_gang_mianzi() == []

    def test_angang_manzu(self):
        assert _shoupai('m1111p456s789z1234').get_gang_mianzi() == ['m1111']

    def test_angang_pinzu(self):
        assert _shoupai('m123p4444s789z1234').get_gang_mianzi() == ['p4444']

    def test_angang_sohzu(self):
        assert _shoupai('m123p456s7777z1234').get_gang_mianzi() == ['s7777']

    def test_angang_zipai(self):
        assert _shoupai('m123p456s789z11112').get_gang_mianzi() == ['z1111']

    def test_angang_include_hongpai(self):
        assert _shoupai('m123p0555s789z1234').get_gang_mianzi() == ['p5550']
        assert _shoupai('m123p0055s789z1234').get_gang_mianzi() == ['p5500']
        assert _shoupai('m123p0005s789z1234').get_gang_mianzi() == ['p5000']
        assert _shoupai('m123p0000s789z1234').get_gang_mianzi() == ['p0000']

    def test_angang_abandoned_zimo(self):
        assert _shoupai('m111p456s789z1122m1').get_gang_mianzi() == ['m1111']

    def test_angang_lizhied(self):
        assert _shoupai('m111123p456s78z11m4*').get_gang_mianzi() == []

    def test_angang_multi(self):
        assert _shoupai('m1111p456s789z1111').get_gang_mianzi() == ['m1111', 'z1111']

    def test_gagang_ng_after_dapai(self):
        assert _shoupai('m1p555s999z123,m111-').get_gang_mianzi() is None
        assert _shoupai('m1p555s999,z333=,m111-').get_gang_mianzi() is None

    def test_gagang_ng_after_fulou(self):
        assert _shoupai('m12p555s999,z333=,m111-,').get_gang_mianzi() is None
        assert _shoupai('__________,m111-,').get_gang_mianzi() is None

    def test_gagang_noexist(self):
        assert _shoupai('m123p456s789z12,z777+').get_gang_mianzi() == []
        assert _shoupai('___________,z777+').get_gang_mianzi() == []

    def test_gagang_manzu(self):
        assert _shoupai('m1p456s789z1234,m111+').get_gang_mianzi() == ['m111+1']

    def test_gagang_pinzu(self):
        assert _shoupai('m123p4s789z1234,p444=').get_gang_mianzi() == ['p444=4']

    def test_gagang_sohzu(self):
        assert _shoupai('m123p456s7z1234,s777-').get_gang_mianzi() == ['s777-7']

    def test_gagang_zipai(self):
        assert _shoupai('m123p456s789z12,z111+').get_gang_mianzi() == ['z111+1']

    def test_gagang_by_hongpai(self):
        assert _shoupai('m123p0s789z1234,p555=').get_gang_mianzi() == ['p555=0']

    def test_gagang_include_hongpai(self):
        assert _shoupai('m123p5s789z1234,p550-').get_gang_mianzi() == ['p550-5']

    def test_gagang_cannot_after_lizhi(self):
        assert _shoupai('p456s789z1234m1*,m111+').get_gang_mianzi() == []

    def test_gagang_multi(self):
        assert _shoupai('m1p4s789z123,m111+,p444=').get_gang_mianzi() == ['m111+1', 'p444=4']

    def test_angang_and_gagang(self):
        assert _shoupai('m1p456s789z1111,m111+').get_gang_mianzi() == ['m111+1', 'z1111']
