import hashlib
import uuid
import time
import requests
import json
from api_key import *


# 文本翻译
def text2text_translate(words, model="youdao",src_lang="ja",target_lang="zh-CHS"):
    if model == "youdao":
        def encrypt(signStr):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(signStr.encode('utf-8'))
            return hash_algorithm.hexdigest()

        def truncate(q):
            if q is None:
                return None
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

        def do_request(data):
            youdao_url = 'https://openapi.youdao.com/api'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            return requests.post(youdao_url, data=data, headers=headers)
        q = words
        data = {}
        data['from'] = src_lang         # 翻译源语言
        data['to'] = target_lang       # 翻译目标语言
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime  # 时间戳
        salt = str(uuid.uuid1())
        signStr = youdao_Id + truncate(q) + salt + curtime + youdao_key
        sign = encrypt(signStr)
        data['appKey'] = youdao_Id      # 应用ID
        data['q'] = q                   # 翻译语句
        data['salt'] = salt
        data['sign'] = sign
        response = do_request(data)

        # 回复解码
        json_data = response.content.decode('utf-8')
        data = json.loads(json_data)
        translation = data['translation']

    return translation[0]
