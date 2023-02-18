import pytest   # noqa

from jongpy.core.shoupai import Shoupai
from jongpy.core.hule import hule_mianzi, hule
from jongpy.core.hule import hule_param as param
from jongpy.core.exceptions import InvalidOperationError


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


class TestHuleFu:

    def test_invalid_param(self):
        with pytest.raises(InvalidOperationError):
            hule(Shoupai.from_str(), 'm1', param())

    def test_not_hule(self):
        h = hule(Shoupai.from_str(), None, param())
        assert h is None

    def test_fu_pinghu_zimo(self):
        h = hule(Shoupai.from_str('m345567p234s33789'), None, param())
        assert h['fu'] == 20

    def test_fu_pinghu_rong(self):
        h = hule(Shoupai.from_str('m345567p234s3378'), 's9=', param())
        assert h['fu'] == 30

    def test_fu_otafeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z33s78'), 's9=', param())
        assert h['fu'] == 30

    def test_fu_zhuanfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z11s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_menfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z22s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_sanyuan_jiangpai(self):
        h = hule(Shoupai.from_str('m112233p456z55s78'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_zhuanfeng_and_menfeng_jiangpai(self):
        h = hule(Shoupai.from_str('m112233z444z11s78'), 's9=', param({'menfeng': 0}))
        assert h['fu'] == 50

    def test_fu_zhungzhang_minkezi(self):
        h = hule(Shoupai.from_str('m123z11m88,p888+,s888-'), 'm8=', param({'menfeng': 0}))
        assert h['fu'] == 30

    def test_fu_yaojiu_minkezi(self):
        h = hule(Shoupai.from_str('m123p22s99,z222+,p111-'), 's9=', param())
        assert h['fu'] == 40

    def test_fu_zhungzhang_ankezi(self):
        h = hule(Shoupai.from_str('z33p222777s888m23'), 'm4=', param())
        assert h['fu'] == 50

    def test_fu_yaojiu_ankezi(self):
        h = hule(Shoupai.from_str('s33p111999z555m23'), 'm4=', param())
        assert h['fu'] == 60

    def test_fu_zhungzhang_mingang(self):
        h = hule(Shoupai.from_str('p33m22245667,s444+4'), 'm8=', param())
        assert h['fu'] == 40

    def test_fu_yaojiu_mingang(self):
        h = hule(Shoupai.from_str('p33m23445667,z6666-'), 'm8=', param())
        assert h['fu'] == 40

    def test_fu_zhungzhang_angang(self):
        h = hule(Shoupai.from_str('p33m23445667,s4444'), 'm8=', param())
        assert h['fu'] == 50

    def test_fu_yaojiu_angang(self):
        h = hule(Shoupai.from_str('p33m23445667,z7777'), 'm8=', param())
        assert h['fu'] == 70

    def test_fu_zimo(self):
        h = hule(Shoupai.from_str('p33m222s222345,s888-'), None, param())
        assert h['fu'] == 40

    def test_fu_danqi(self):
        h = hule(Shoupai.from_str('m222s222345p3,s888-'), 'p3=', param())
        assert h['fu'] == 40

    def test_fu_kanzhang(self):
        h = hule(Shoupai.from_str('p33m222s22235,s888-'), 's4=', param())
        assert h['fu'] == 40

    def test_fu_bianzhang(self):
        h = hule(Shoupai.from_str('p33z111m12389,s222-'), 'm7=', param())
        assert h['fu'] == 40

    def test_fu_fulou_pinghu(self):
        h = hule(Shoupai.from_str('m22p345678s34,s67-8'), 's5=', param())
        assert h['fu'] == 30

    def test_fu_qidui(self):
        h = hule(Shoupai.from_str('m2255p88s1166z1155'), None, param())
        assert h['fu'] == 25

    def test_fu_goushi(self):
        h = hule(Shoupai.from_str('m19p19s1z12345677s9'), None, param())
        assert h['fu'] is None

    def test_fu_jiulian(self):
        h = hule(Shoupai.from_str('m11123456789995'), None, param())
        assert h['fu'] is None


class TestHuleHupai:

    def test_no_hupai(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param())
        assert h['hupai'] is None

    def test_hupai_lizhi(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1}]

    def test_hupai_double_lizhi(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 2}))
        assert h['hupai'] == [{'name': 'ダブル立直', 'fanshu': 2}]

    def test_hupai_lizhi_yifa(self):
        h = hule(Shoupai.from_str('m344556s24678z66*'), 's3=', param({'lizhi': 1, 'yifa': True}))
        assert h['hupai'] == [{'name': '立直', 'fanshu': 1},
                              {'name': '一発', 'fanshu': 1}]

    def test_hupai_haidi_zimo(self):
        h = hule(Shoupai.from_str('m344556s24z66s3,s6-78'), None, param({'haidi': 1}))
        assert h['hupai'] == [{'name': '海底摸月', 'fanshu': 1}]

    def test_hupai_haidi_rong(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param({'haidi': 2}))
        assert h['hupai'] == [{'name': '河底撈魚', 'fanshu': 1}]

    def test_hupai_lingshang(self):
        h = hule(Shoupai.from_str('m344556s24z66s3,s777+7'), None, param({'lingshang': True}))
        assert h['hupai'] == [{'name': '嶺上開花', 'fanshu': 1}]

    def test_hupai_qianggang(self):
        h = hule(Shoupai.from_str('m344556s24678z66'), 's3=', param({'qianggang': True}))
        assert h['hupai'] == [{'name': '槍槓', 'fanshu': 1}]

    def test_hupai_tianhu(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param({'tianhu': 1}))
        assert h['hupai'] == [{'name': '天和', 'fanshu': '*'}]

    def test_hupai_zhihu(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param({'tianhu': 2}))
        assert h['hupai'] == [{'name': '地和', 'fanshu': '*'}]

    def test_hupai_menqianging(self):
        h = hule(Shoupai.from_str('m344556s24678z66s3'), None, param())
        assert h['hupai'] == [{'name': '面前清自摸和', 'fanshu': 1}]

    def test_hupai_zhuangfeng_dong(self):
        h = hule(Shoupai.from_str('m345567s3378z111'), 's9=', param())
        assert h['hupai'] == [{'name': '場風 東', 'fanshu': 1}]

    def test_hupai_menfeng_xi(self):
        h = hule(Shoupai.from_str('m345567s33789,z333+'), None, param({'menfeng': 2}))
        assert h['hupai'] == [{'name': '自風 西', 'fanshu': 1}]

    def test_hupai_zhuangfeng_and_menfeng_nan(self):
        h = hule(Shoupai.from_str('m345567s33z22,s789-'), 'z2=', param({'zhuangfeng': 1}))
        assert h['hupai'] == [{'name': '場風 南', 'fanshu': 1},
                              {'name': '自風 南', 'fanshu': 1}]

    def test_hupai_fanpai_hak(self):
        h = hule(Shoupai.from_str('m345567s33789,z555+5'), None, param())
        assert h['hupai'] == [{'name': '翻牌 白', 'fanshu': 1}]

    def test_hupai_fanpai_fa_chun(self):
        h = hule(Shoupai.from_str('m345567s33,z6666+,z7777'), None, param())
        assert h['hupai'] == [{'name': '翻牌 發', 'fanshu': 1},
                              {'name': '翻牌 中', 'fanshu': 1}]

    def test_hupai_pinghu(self):
        h = hule(Shoupai.from_str('z33m234456p78s123'), 'p9=', param())
        assert h['hupai'] == [{'name': '平和', 'fanshu': 1}]

    def test_hupai_pinghu_zimo(self):
        h = hule(Shoupai.from_str('z33m234456p78s123p9'), None, param())
        assert h['hupai'] == [{'name': '面前清自摸和', 'fanshu': 1},
                              {'name': '平和', 'fanshu': 1}]

    def test_hupai_fulou_pinghu(self):
        h = hule(Shoupai.from_str('z33m234456p78,s1-23'), 'p9=', param())
        assert h['hupai'] is None

    def test_hupai_danyaojiu(self):
        h = hule(Shoupai.from_str('m22555p234s78,p777-'), 's6=', param())
        assert h['hupai'] == [{'name': '断ヤオ九', 'fanshu': 1}]

    def test_hupai_danyaojiu_qiduizi(self):
        h = hule(Shoupai.from_str('m2255p4488s33667'), 's7=', param())
        assert h['hupai'] == [{'name': '断ヤオ九', 'fanshu': 1},
                              {'name': '七対子', 'fanshu': 2}]

    def test_hupai_yibeikou(self):
        h = hule(Shoupai.from_str('m33455p111s33789'), 'm4=', param())
        assert h['hupai'] == [{'name': '一盃口', 'fanshu': 1}]

    def test_hupai_fulou_yibeikou(self):
        h = hule(Shoupai.from_str('m33455p111s33,s78-9'), 'm4=', param())
        assert h['hupai'] is None

    def test_hupai_sansetongshun(self):
        h = hule(Shoupai.from_str('m567p567s2256799'), 's9=', param())
        assert h['hupai'] == [{'name': '三色同順', 'fanshu': 2}]

    def test_hupai_fulou_sansetongshun(self):
        h = hule(Shoupai.from_str('m567s2256799,p56-7'), 's9=', param())
        assert h['hupai'] == [{'name': '三色同順', 'fanshu': 1}]

    def test_hupai_yiqitongguan(self):
        h = hule(Shoupai.from_str('m12456789s33789'), 'm3=', param())
        assert h['hupai'] == [{'name': '一気通貫', 'fanshu': 2}]

    def test_hupai_fulou_yiqitongguan(self):
        h = hule(Shoupai.from_str('m12789s33789,m4-56'), 'm3=', param())
        assert h['hupai'] == [{'name': '一気通貫', 'fanshu': 1}]

    def test_hupai_hunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m123999p789z33s12'), 's3=', param())
        assert h['hupai'] == [{'name': '混全帯ヤオ九', 'fanshu': 2}]

    def test_hupai_fulou_hunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m123p789z33s12,m999+'), 's3=', param())
        assert h['hupai'] == [{'name': '混全帯ヤオ九', 'fanshu': 1}]

    def test_hupai_qiduizi(self):
        h = hule(Shoupai.from_str('m115599p2233s8z22'), 's8=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2}]

    def test_hupai_duiduihu(self):
        h = hule(Shoupai.from_str('m55888z333s22,p111='), 's2=', param())
        assert h['hupai'] == [{'name': '対々和', 'fanshu': 2}]

    def test_hupai_sananke(self):
        h = hule(Shoupai.from_str('p99s111m555,p345-,s3333'), None, param())
        assert h['hupai'] == [{'name': '三暗刻', 'fanshu': 2}]

    def test_hupai_sangangzi(self):
        h = hule(Shoupai.from_str('p11m45,s2222+,m888=8,z4444'), 'm3=', param())
        assert h['hupai'] == [{'name': '三槓子', 'fanshu': 2}]

    def test_hupai_sansetongke(self):
        h = hule(Shoupai.from_str('s12377m22,p222-,s222-'), 'm2=', param())
        assert h['hupai'] == [{'name': '三色同刻', 'fanshu': 2}]

    def test_hupai_hunlaotou_duiduihu(self):
        h = hule(Shoupai.from_str('z11p11199,m111=,z333+'), 'p9=', param())
        assert h['hupai'] == [{'name': '対々和', 'fanshu': 2},
                              {'name': '混老頭', 'fanshu': 2}]

    def test_hupai_hunlaotou_qiduizi(self):
        h = hule(Shoupai.from_str('m1199p11s99z11335'), 'z5=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '混老頭', 'fanshu': 2}]

    def test_hupai_xiaosanyuan(self):
        h = hule(Shoupai.from_str('z55577m567p22,z666-'), 'p2=', param())
        assert h['hupai'] == [{'name': '翻牌 白', 'fanshu': 1},
                              {'name': '翻牌 發', 'fanshu': 1},
                              {'name': '小三元', 'fanshu': 2}]

    def test_hupai_hunyise(self):
        h = hule(Shoupai.from_str('m111234789z1133'), 'z3=', param())
        assert h['hupai'] == [{'name': '混一色', 'fanshu': 3}]

    def test_hupai_fulou_hunyise(self):
        h = hule(Shoupai.from_str('z11333p23478,p111+'), 'p9=', param())
        assert h['hupai'] == [{'name': '混一色', 'fanshu': 2}]

    def test_hupai_hunyise_qiduizi(self):
        h = hule(Shoupai.from_str('s11224488z22557'), 'z7=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '混一色', 'fanshu': 3}]

    def test_hupai_chunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m11s123p789s789m99'), 'm9=', param())
        assert h['hupai'] == [{'name': '純全帯ヤオ九', 'fanshu': 3}]

    def test_hupai_fulou_chunquandaiyaojiu(self):
        h = hule(Shoupai.from_str('m11s123p789s78,m999='), 's9=', param())
        assert h['hupai'] == [{'name': '純全帯ヤオ九', 'fanshu': 2}]

    def test_hupai_erbeiko(self):
        h = hule(Shoupai.from_str('m223344p667788s9'), 's9=', param())
        assert h['hupai'] == [{'name': '二盃口', 'fanshu': 3}]

    def test_hupai_erbeiko_4pais(salf):
        h = hule(Shoupai.from_str('m222233334444s9'), 's9=', param())
        assert h['hupai'] == [{'name': '二盃口', 'fanshu': 3}]

    def test_hupai_fulou_erbeiko(self):
        h = hule(Shoupai.from_str('m223344p678s9,p678-'), 's9=', param())
        assert h['hupai'] is None

    def test_hupai_qingyise(self):
        h = hule(Shoupai.from_str('m1113456677778'), 'm9=', param())
        assert h['hupai'] == [{'name': '清一色', 'fanshu': 6}]

    def test_hupai_fulou_qingyise(self):
        h = hule(Shoupai.from_str('p2344555,p12-3,p7-89'), 'p1=', param())
        assert h['hupai'] == [{'name': '清一色', 'fanshu': 5}]

    def test_hupai_qingyise_qiduizi(self):
        h = hule(Shoupai.from_str('s1122445577889'), 's9=', param())
        assert h['hupai'] == [{'name': '七対子', 'fanshu': 2},
                              {'name': '清一色', 'fanshu': 6}]

    def test_hupai_goushiwushuang(self):
        h = hule(Shoupai.from_str('m119p19s19z1234567'), None, param())
        assert h['hupai'] == [{'name': '国士無双', 'fanshu': '*'}]

    def test_hupai_goushiwushuang_13men(self):
        h = hule(Shoupai.from_str('m19p19s19z1234567m1'), None, param())
        assert h['hupai'] == [{'name': '国士無双十三面', 'fanshu': '**'}]

    def test_hupai_sianke(self):
        h = hule(Shoupai.from_str('m33m111p333s777z111'), None, param())
        assert h['hupai'] == [{'name': '四暗刻', 'fanshu': '*'}]

    def test_hupai_sianke_danqi(self):
        h = hule(Shoupai.from_str('m111p333s777z111m3'), 'm3=', param())
        assert h['hupai'] == [{'name': '四暗刻単騎', 'fanshu': '**'}]

    def test_hupai_dasanyuan(self):
        h = hule(Shoupai.from_str('z555m456p22z66,z777+'), 'z6=', param())
        assert h['hupai'] == [{'name': '大三元', 'fanshu': '*'}]

    def test_hupai_dasanyuan_baojia(self):
        h = hule(Shoupai.from_str('m2234,z555-5,z6666,z777+'), 'm5=', param())
        assert h['hupai'] == [{'name': '大三元', 'fanshu': '*', 'baojia': '+'}]

    def test_hupai_shosixi(self):
        h = hule(Shoupai.from_str('m234z2244,z333+,z111-'), 'z4=', param())
        assert h['hupai'] == [{'name': '小四喜', 'fanshu': '*'}]

    def test_hupai_daisixi(self):
        h = hule(Shoupai.from_str('m22z22244,z333+,z111-'), 'z4=', param())
        assert h['hupai'] == [{'name': '大四喜', 'fanshu': '**'}]

    def test_hupai_daisixi_baojia(self):
        h = hule(Shoupai.from_str('m2,z222+,z4444,z333+,z111-'), 'm2=', param())
        assert h['hupai'] == [{'name': '大四喜', 'fanshu': '**', 'baojia': '-'}]

    def test_hupai_ziyise(self):
        h = hule(Shoupai.from_str('z1112277,z555=,z444+'), 'z7=', param())
        assert h['hupai'] == [{'name': '字一色', 'fanshu': '*'}]

    def test_hupai_ziyise_qiduizi(self):
        h = hule(Shoupai.from_str('z1122334455667'), 'z7=', param())
        assert h['hupai'] == [{'name': '字一色', 'fanshu': '*'}]

    def test_hupai_lvyise(self):
        h = hule(Shoupai.from_str('s22334466z66,s888+'), 'z6=', param())
        assert h['hupai'] == [{'name': '緑一色', 'fanshu': '*'}]

    def test_hupai_lvyise_without_fa(self):
        h = hule(Shoupai.from_str('s4466,s222=,s333+,s888-'), 's6=', param())
        assert h['hupai'] == [{'name': '緑一色', 'fanshu': '*'}]

    def test_hupai_qinglaotou(self):
        h = hule(Shoupai.from_str('s11p111m11,s999-,m999='), 'm1=', param())
        assert h['hupai'] == [{'name': '清老頭', 'fanshu': '*'}]

    def test_hupai_sigangzi(self):
        h = hule(Shoupai.from_str('m1,z5555,p222+2,p777-7,s1111-'), 'm1=', param())
        assert h['hupai'] == [{'name': '四槓子', 'fanshu': '*'}]

    def test_hupai_jiulianbaodeng(self):
        h = hule(Shoupai.from_str('m1112235678999'), 'm4=', param())
        assert h['hupai'] == [{'name': '九蓮宝燈', 'fanshu': '*'}]

    def test_hupai_pure_jiulianbaodeng(self):
        h = hule(Shoupai.from_str('m1112345678999'), 'm2=', param())
        assert h['hupai'] == [{'name': '純正九蓮宝燈', 'fanshu': '**'}]
