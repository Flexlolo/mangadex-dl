"""
Usage:
    mangadex-dl MANGA_ID [options]

Options:
  -g, --group GID       Only download chapters from specified group
  -c, --chapter NUM     Only download specified chapter number
  -e, --extra EXTRA     Extra information to be added in folder names

Download manga chapters
"""
from collections import defaultdict
from typing import Dict, List
import os
import sys

from docopt import docopt
import requests
import toml

from api import API


def get_manga_name(manga_id: str) -> str:
    r = API.request('GET', f'manga/{manga_id}')

    for title in r['data']['attributes']['altTitles']:
        if 'ja-ro' in title:
            return title['ja-ro']

GROUP_NAME_CACHE = {}

def get_group_name(group_id: str, use_cache: bool = True) -> str:
    global GROUP_NAME_CACHE

    if group_id in GROUP_NAME_CACHE:
        return GROUP_NAME_CACHE[group_id]

    r = API.request('GET', f'group/{group_id}')

    group_name = r['data']['attributes']['name']
    GROUP_NAME_CACHE[group_id] = group_name

    return group_name

def get_chapter_group(chapter_id: str) -> str:
    for rel in r['data']['attributes']['relationships']:
        if rel['type'] == 'scanlation_group':
            return rel['id']

    return ''

def get_manga_chapters(manga_id: str, group_id: str) -> Dict[str, str]:
    params = {}

    if group_id:
        params = {
            'groups[]': [group_id]
        }

    r = API.request('GET', f'manga/{manga_id}/aggregate', params=params)

    chapters = {}

    for volume in r['volumes'].values():
        for chapter in volume['chapters'].values():
            chapters[chapter['chapter']] = chapter['id']

    return chapters

def get_chapter_images(chapter_id: str, quality: str = 'data') -> List[str]:
    r = API.request('GET', f'at-home/server/{chapter_id}')
    base_url = r['baseUrl']
    chapter_hash = r['chapter']['hash']

    images = []

    for file in r['chapter'][quality]:
        url = '/'.join([base_url, quality, chapter_hash, file])
        images.append(url)

    return images

def chapter_folder_format(name: str, num: str, group_name: str, extra: str = '') -> str:
    if num.find('.') != -1:
        num = num.split('.')[0].zfill(3) + '.' + num.split('.')[1]
    else:
        num = num.zfill(3)

    if extra: 
        return f'{name} - c{num} ({extra}) [{group_name}]'

    return f'{name} - c{num} [{group_name}]'




def main():
    args = docopt(__doc__)

    manga_id = args['MANGA_ID']
    group_id = args['--group'] if args['--group'] else ''
    chapter_num = args['--chapter'] if args['--chapter'] else ''
    extra = args['--extra'] if args['--extra'] else ''

    manga_name = get_manga_name(manga_id)
    print('Manga:', manga_name)

    path = manga_name.replace(os.sep, '')
    os.makedirs(path, exist_ok=True)

    chapters = get_manga_chapters(manga_id, group_id)

    if chapter_num:
        if chapter_num not in chapters:
            print('Specified chapter number is not found in a list.')
            return

        chapters = {chapter_num: chapters[chapter_num]}

    for (chapter, chapter_id) in reversed(chapters.items()):
        if group_id:
            chapter_group_id = group_id
        else:
            chapter_group_id = get_chapter_group(chapter_id)

        group_name = get_group_name(chapter_group_id)

        chapter_folder = chapter_folder_format(manga_name, chapter, group_name, extra)
        print(f"Getting '{chapter_folder}'")

        chapter_folder = chapter_folder.replace(os.sep, '')
        chapter_path = os.path.join(path, chapter_folder)
        os.makedirs(chapter_path, exist_ok=True)

        images = get_chapter_images(chapter_id)

        for i, image_url in enumerate(images):
            filename = str(i).zfill(3) + '.png' 
            file = os.path.join(chapter_path, filename)

            if os.path.exists(file):
                continue

            print(file)
            r = requests.get(image_url)

            with open(file, 'wb') as f:
                f.write(r.content)

try:
    main()
except KeyboardInterrupt:
    print('\nInterrupted.')
    sys.exit(130)