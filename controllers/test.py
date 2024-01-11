# coding=utf-8
import json

from six import string_types
from six.moves.urllib.parse import urlencode, urlunparse  # noqa

import requests


def post(json_str, video_file_args):
    url = 'https://business-api.tiktok.com/open_api/v1.3/file/video/ad/upload/'
    args = json_str
    headers = {
        "Access-Token": '41a6ae93ac0097a44ca52bd2df8651b2bcb5f020',
        # "Content-Type": "multipart/form-data"
    }

    rsp = requests.post(url, data=args, headers=headers, files=video_file_args)

    print(rsp)

    return rsp.json()


if __name__ == '__main__':
    advertiser_id = '7317127691797430274'
    video_file = open('/home/adpttq113/Downloads/vid.mp4', "rb")
    video_signature = '1c679a93a5357ace35f3a56d4cca8b89'

    my_args = {
        'advertiser_id': advertiser_id,
        'video_signature': video_signature,
    }
    video_file_args = {"video_file": video_file}
    print(post(my_args, video_file_args))

