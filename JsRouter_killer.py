import sys

import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


def url_filter(js_url):
    pattern = r'^https?://'
    if not re.search(pattern, js_url):
        js_url = 'https://' + js_url.lstrip('/')
    return js_url


def extract_js_files(url):
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the webpage.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tags = soup.find_all('script', src=True)
    js_files = [script['src'] for script in script_tags]
    return js_files


def process_js_file(js_url):
    js_url = url_filter(js_url)
    response = requests.get(js_url)
    if response.status_code != 200:
        print("Failed to retrieve the JavaScript file:", js_url)
        return None
    return response.text

def determine(js_content):
    if ".async." in js_content:
        return True
    else:
        return False

def extract_content(js_content):
    js_contents = js_content
    if "webpack" in js_content:
        deter = determine(js_contents)
        pattern = r'(?:"?)(\d+)(?:"?):(?:"([^"]+)"|(\w+))'
        matches = re.findall(pattern, js_content)

        return [(match, deter) for match in matches]
        # return  matches
    else:
        return [((0, 0), False)]


def remove_last_path_segment(url):
    url = url_filter(url)
    parsed_url = urllib.parse.urlparse(url)
    path = parsed_url.path
    path_segments = path.split('/')
    new_path = '/'.join(path_segments[:-1])
    new_url = urllib.parse.urlunparse(parsed_url._replace(path=new_path))
    if '#' in new_url:
        new_url = new_url.split('#')[0]
    return new_url


def count_dots(url):
    url = url_filter(url)
    pattern = r'https?://[^/]+(.+)'
    match = re.search(pattern, url)
    if match:
        path = match.group(1)
        filename = re.search(r'/([^/]+)$', path)
        dot_count = filename.group().count('.')
        return dot_count
    else:
        return 0
def append_to_url(url, dot_count, key_value_pairs,deters,b):
    urls=[]
    if deters!=True:
        if dot_count == 1:
            url += f"/{key_value_pairs[1]}.js"
            urls.append(url)
        elif dot_count == 2:
            url += f"/{key_value_pairs[0]}.{key_value_pairs[1]}.js"
            urls.append(url)
    else:
        if dot_count == 1:
            url += f"/{key_value_pairs[1]}.async.js"
            urls.append(url)
        elif dot_count == 2:
            if "__" in key_value_pairs[1]:
                search_result_one=search_TwoList(key_value_pairs[0],b)
                search_result_two=search_TwoList2(search_result_one[0],b)
                if len(search_result_two)>1:
                    for i in search_result_two:
                        url += f"/{search_result_one[1]}.{i}.async.js"
                        urls.append(url)
                else:
                    url += f"/{search_result_one[1]}.{search_result_two[0]}.async.js"
                    urls.append(url)
            else:
                url += f"/{key_value_pairs[0]}.{key_value_pairs[1]}.async.js"
                urls.append(url)
    return urls


def search_TwoList(str1,b):
    for sublist in b:
        for item in sublist:
            if item == str1:
                return b[b.index(sublist)]

def search_TwoList2(str1, b):
    matches = []
    for sublist in b:
        for item in sublist:
            if item == str1:
                pattern = r'\b[a-zA-Z0-9]+\b'
                text = b[b.index(sublist)][sublist.index(item) + 1]
                result = re.match(pattern, text)
                if result:
                    matches.append(text)
    return matches


def check_url(url):
    status = requests.session().head(url).status_code
    if status == 200:
        return (url, status)
    else:
        return None

if __name__ == '__main__':
    print("JsRouter_killer")
    pattern = r'[^a-zA-Z0-9_.]'
    url=sys.argv[1]
    js_files = extract_js_files(url)
    b=[]
    for js_file in js_files:
        js_url = str(js_file)
        try:
            js_content = process_js_file(js_url)
        except:
            continue
        matches_deters = set(extract_content(js_content))
        for match, deter in matches_deters:
            if str(match[1]) != "":
                c = []
                c.append(match[0])
                c.append(match[1])
                b.append(c)
        for matchs,deters in tqdm(matches_deters,desc="Processing JS files",position=0, leave=True):
            new_url = remove_last_path_segment(js_url)
            dot_count = count_dots(js_url)
            if dot_count > 3:
                continue
            new_url = append_to_url(new_url, dot_count, matchs, deters, b)
            if len(new_url)>1:
                with ThreadPoolExecutor() as executor:
                    results = list(executor.map(check_url, new_url))
                for result in results:
                    if result:
                        print(result[0])
            elif "#" not in new_url[0]:
                status = requests.head(new_url[0]).status_code
                if status == 200:
                    print(new_url[0])
            else:
                pass
