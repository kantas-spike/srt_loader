# -*- coding: utf-8 -*-
import json
from io import open
import copy


def read_config_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def merge_settings(config1, config2):
    merged = {}
    # キーの一覧取得
    for key in set(config1.keys()) | set(config2.keys()):
        # if 両方にキーが存在
        if key in config1 and key in config2:
            #  値の型が同じ
            if type(config1[key]) == type(config2[key]):
                # if 型がdictやlist以外
                if not (
                    isinstance(config1[key], dict) or isinstance(config1[key], list)
                ):
                    # config2側を採用
                    merged[key] = config2[key]
                # elif dict
                elif isinstance(config1[key], dict):
                    # merge_settings(config1側、 config2)を採用
                    merged[key] = merge_settings(config1[key], config2[key])
                # else
                else:
                    merged[key] = []
                    # config2側のlistの要素分だけ以下を実行
                    for idx, elm in enumerate(config2[key]):
                        # if 要素の型がdict
                        if isinstance(config1[key], dict):
                            # merge_settings(config1側、 config2側)を採用
                            merged[key].append(
                                merge_settings(config1[key][idx], config2[key][idx])
                            )
                        # else
                        else:
                            # config2の要素を採用
                            merged[key].append(copy.copy(config2[key][idx]))
            # 値の型が異なる
            else:
                # config2側を採用
                merged[key] = copy.copy(config2[key])
        # elif config1側にのみ存在
        elif key in config1:
            # config1側を採用
            merged[key] = copy.copy(config1[key])
        # else config2側にのみ存在
        else:
            # config2側を採用
            merged[key] = copy.copy(config2[key])
    return merged
