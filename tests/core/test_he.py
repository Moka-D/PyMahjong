import pytest

from jongpy.core.he import He
from jongpy.core.exceptions import (PaiFormatError,
                                    MianziFormatError,
                                    InvalidOperationError)


class TestHe:

    @pytest.fixture
    def setup(self):
        self._he = He()

    def test_exist_class(self):
        assert He()

    def test_init_pai_length(self):
        assert len(He()._pai) == 0

    def test_dapai_invalid_pai(self):
        with pytest.raises(PaiFormatError):
            He().dapai('z8')

    def test_dapai_pai_length(self, setup):
        assert len(self._he._pai) + 1 == len(self._he.dapai('m1')._pai)

    def test_dapai_abandon_zimo(self):
        assert He().dapai('m1_')._pai.pop() == 'm1_'

    def test_dapai_lizhi(self):
        assert He().dapai('m1*')._pai.pop() == 'm1*'

    def test_dapai_abandon_zimo_lizhi(self):
        assert He().dapai('m1_*')._pai.pop() == 'm1_*'

    def test_fulou_invalid_mianzi(self):
        with pytest.raises(MianziFormatError):
            He().dapai('m1').fulou('m1-')
        with pytest.raises(InvalidOperationError):
            He().dapai('m1').fulou('m1111')
        with pytest.raises(InvalidOperationError):
            He().dapai('m1').fulou('m12-3')

    def test_fulou_pai_length(self, setup):
        self._he.dapai('m1_')
        assert len(self._he._pai) == len(self._he.fulou('m111+')._pai)

    def test_fulou_who(self, setup):
        self._he.dapai('m2*')
        assert self._he.fulou('m12-3')._pai.pop() == 'm2*-'

    def test_find_pai(self, setup):
        assert self._he.dapai('m1').find('m1')

    def test_find_abandoned_zimo(self, setup):
        assert self._he.dapai('m2_').find('m2')

    def test_find_lizhied(self, setup):
        assert self._he.dapai('m3*').find('m3')

    def test_find_hongpai(self, setup):
        assert self._he.dapai('m0').find('m5')

    def test_find_fuloued(self, setup):
        assert self._he.dapai('m4_').fulou('m234-').find('m4')

    def test_find_unnormalized(self, setup):
        assert self._he.dapai('m0').find('m0_*')
