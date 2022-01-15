from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from bs4 import BeautifulSoup

from cairosvg.surface import PDFSurface
from cairosvg.parser import Tree
from cairosvg import svg2pdf

from typing import Union, Optional
from io import BytesIO
from tqdm import tqdm

# import proxyscrape
import threading
import cairocffi
import requests
import json
import time
import os

class PageNotFound(Exception):
    pass

def download(user: Optional[Union[int, str]] = None,
             score: Optional[Union[int, str]] = None,
             url: Optional[str] = None,
             dpi: int = 40):
    def fetch(src):
        nonlocal results, pbar
        resp = requests.get(src, stream = True)
        data = resp.content
        surf = PDFSurface(Tree(bytestring = data), None, dpi)
        results[src] = surf
        pbar.update(1)

    if url is None:
        if user is None:
            url = f"https://musescore.com/score/{score}"
        else:
            url = f"https://musescore.com/user/{user}/scores/{score}"

    if not os.path.exists('scores'):
        os.mkdir('scores')

    # collector = proxyscrape.create_collector('default', 'http')
    # proxy = collector.get_proxy({'country': 'united states', 'anonymous': True})

    try:
        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument("--window-size=1920,1080")
        # options.add_argument(f'--proxy-server={proxy.host}:{proxy.port}')

        driver = webdriver.Chrome(options = options)
        driver.get(url)

        resp = requests.get(url)

        if resp.status_code == 404:
            raise PageNotFound("The score could not be found.")

        while True:
            try:
                title = driver.find_element_by_class_name('_3ke60').text
                pages = len(driver.find_element_by_class_name('JQKO_').find_elements_by_xpath("*")) - 2
                fpath = os.path.join('scores', title + '.pdf')
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(0.1)
                continue

        surface = cairocffi.PDFSurface(fpath, 1, 1)
        context = cairocffi.Context(surface)

        urls = []
        pbar = tqdm(desc = 'Fetching URLs to svg image of each page in score', total = pages, leave = False)

        for page in range(pages):
            driver.execute_script(f'document.getElementsByClassName("vAVs3")[{page}].scrollIntoView()')
            sheet = driver.find_elements_by_class_name('vAVs3')[page]

            while True:
                try:
                    src = sheet.find_elements_by_xpath("*")[0].get_attribute('src')

                    if src is None:
                        continue

                    urls.append(src)
                    pbar.update(1)

                    break
                except KeyboardInterrupt:
                    break
                except:
                    continue

        results = {}
        threads = []

        pbar = tqdm(desc = 'Fetching image contents', total = pages, leave = False)

        for src in urls:
            thread = threading.Thread(target = fetch, args = (src,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        for src in tqdm(urls, 'Constructing PDF', leave = False):
            image_surface = results[src]
            surface.set_size(image_surface.width, image_surface.height)
            context.set_source_surface(image_surface.cairo, 0, 0)
            context.paint()
            surface.show_page()
    except:
        os.remove(fpath)
    finally:
        try:
            surface.finish()
        except:
            pass

        try:
            driver.close()
        except:
            pass
