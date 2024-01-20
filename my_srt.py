# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import os
import re
from io import open


def time_to_delta(t):
    return timedelta(
        hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond
    )


def read_srt_file(path):
    """
    字幕ファイルを読み込む

    :param str path: 字幕ファイル(SubRip形式)のパス
    :return itemのリスト
            itemは以下の形式
            {"no": 1からの連番,
             "time_info": {"start": timedelta, "end": timedelter},
             "lines": 字幕文字列の配列 }
    """
    item_list = []
    with open(path, encoding="utf-8") as f:
        item = {}
        for line_with_sep in f:
            line = line_with_sep.rstrip(os.linesep)
            if len(line) == 0:
                if len(item) > 0:
                    item_list.append(item)
                    item = {}
            elif len(item) == 0:
                item["no"] = int(line)
            elif len(item) == 1:
                if "-->" not in line:
                    raise ValueError("Bad time format:{}".format(item))
                item["time_info"] = parse_line_of_time(line)
            elif len(item) == 2:
                item["lines"] = []
                item["lines"].append(line)
            elif len(item) == 3:
                item["lines"].append(line)

        if len(item) > 0:
            item_list.append(item)

    return item_list


def parse_line_of_time(line):
    m = re.match(r"\A(\d+:\d+:\d+,\d+) *--> *(\d+:\d+:\d+,\d+) *(.+)?", line)
    results = {}
    if m:
        for k, t in [["start", m.group(1)], ["end", m.group(2)]]:
            if t:
                results[k] = time_to_delta(datetime.strptime(t, "%H:%M:%S,%f"))
            else:
                results[k] = None
        if m.group(3):
            extras = m.group(3)
            if "JSON:" in extras:
                json_data = json.loads(extras.split("JSON:")[1].strip())
                results["json"] = json_data
        return results
    else:
        return results


def hex_to_rgba(hex_str):
    if not hex_str.startswith("#"):
        raise ValueError("#から始まる16進を指定してください: {}".format(hex_str))
    hex_len = len(hex_str) - 1
    # 8桁、6桁、4桁、3桁
    if hex_len not in [8, 6, 4, 3]:
        raise ValueError(
            "#RRGGBBAA,#RRGGBB,#RGBA,#RGBのいずれかの形式を指定してください: {}".format(hex_str)
        )

    # 8桁形式 or 6桁形式
    pattern = r"#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})?"
    max_value = 0xFF
    # 4桁形式 or 3桁形式
    if hex_len in [3, 4]:
        pattern = r"#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])?"
        max_value = 0xF
    m = re.match(pattern, hex_str)
    if m:
        return [int(c, 16) / max_value for c in m.groups(hex(max_value))]
    else:
        raise ValueError(
            "#RRGGBBAA,#RRGGBB,#RGBA,#RGBのいずれかの形式を指定してください: {}".format(hex_str)
        )
