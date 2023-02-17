"""jongpy.core.rule"""


def rule(param: dict = {}):

    rule_ = {
        # 点数関連
        'origin_points': 25000,     # 配給原点
        'rank_bounus': ['20.0', '10.0', '-10.0', '-20.0'],  # 順位点

        # 赤牌有無、喰いタンなど
        'hongpai': {'m': 1, 'p': 1, 's': 1},    # 赤牌
        'fulou_duanyaojiu': True,   # 喰いタンあり
        'allow_fulou_slide': 0,     # 喰い替え許可レベル
                                    # 0: 喰い替えなし, 1: スジ喰い替えあり, 2: 現物喰い替えあり

        # 局数関連
        'n_zhuang': 2,  # 場数 0: 一局戦, 1: 東風戦, 2: 東南戦, 3: 一荘戦
        'interrupted_pingju': True,     # 途中流局あり
        'pingju_manguan': True,     # 流し満貫あり
        'declare_no_tingpai': False,    # ノーテン宣言あり
        'penalty_no_tingpai': True,     # ノーテン罰符あり
        'n_max_simultaneous_hule': 2,   # 最大同時和了数
                                        # 1: 頭ハネ, 2: ダブロンあり, 3: トリロンあり
        'continuous_zhuang': 2,     # 連荘方式
                                    # 0: 連荘なし, 1: 和了連荘, 2: テンパイ連荘, 3: ノーテン連荘
        'minus_interruption': True,     # トビ終了あり
        'stop_last_game': True,     # オーラス止めあり
        'extra_game_method': 1,     # 延長戦方式
                                    # 0: なし, 1: サドンデス, 2: 連荘優先サドンデス, 3: 4局固定

        # リーチ・ドラ関連
        'yifa': True,   # 一発あり
        'fubaopai': True,   # 裏ドラあり
        'gang_baopai': True,    # カンドラあり
        'gang_fubaopai': True,  # カン裏あり
        'gang_baopai_delay': True,  # カンドラ後乗せ
        'lizhi_no_zimo': False,     # ツモ番なしリーチあり
        'allow_angang_after_lizhi': 2,  # リーチ後暗槓許可レベル
                                        # 0: 暗槓不可, 1: 牌姿の変わる暗槓不可,
                                        # 2: 待ちの変わる暗槓不可

        # 役満関連
        'compound_damanguan': True,     # 役満の複合あり
        'double_damanguan': True,   # ダブル役満あり
        'counting_damanguan': True,     # 数え役満あり
        'damanguan_baojia': True,   # 役満パオあり
        'ceiled_manguan': True,     # 切り上げ満貫あり
    }

    for key, value in param.items():
        rule_[key] = value

    return rule_
