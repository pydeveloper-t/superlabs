import os.path
import re
import httpx
import aiofiles
from app.api import Base
from dataclasses import dataclass, asdict


@dataclass
class Calculation:
    pair: str
    timeframe: str
    candles: int
    ma: int
    tp: int
    sl: int

    def __post_init__(self):
        if self.pair is None:
            raise ValueError(f"The 'Candles' parameter cannot be blank")
        if self.timeframe is None:
            self.timeframe = '1d'
        if self.timeframe.lower() not in ('5m', '15m', '1h', '4h', '1d', '1w', '1M',):
            raise ValueError(f"The 'Timeframe' parameter must be one of '5m', '15m', '1h', '4h', '1d', '1w', '1M'")
        if self.candles is None:
            self.candles = 10
        if self.ma is None:
            self.ma = 50
        if self.tp is None:
            self.tp = 10
        if self.sl is None:
            self.sl = 15


class Papertrader(Base):
    img_regex = r"<img src=\".\/images\/render-(.*?)\.png\">"
    headers_1 = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://paper-trader.frwd.one',
        'Connection': 'keep-alive',
        'Referer': 'https://paper-trader.frwd.one/',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    headers_2 = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:107.0) Gecko/20100101 Firefox/107.0',
        'Accept': 'image/avif,image/webp,*/*',
        'Accept-Language': 'en-GB,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://paper-trader.frwd.one/',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    def __init__(self, *args: str, **kwargs: str) -> None:
        super().__init__(project_tag=kwargs.get('project_tag', None), basepath=kwargs.get('project_tag', None))
        self.client = httpx.AsyncClient()

    @staticmethod
    def find_regex(pattern: str, searched_string: str) -> str:
        value = ''
        match = re.search(pattern, searched_string, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        if match:
            value = match.groups(0)[0]
        return value

    async def _get_calculation_html_page(self, calculation_param: Calculation) -> str:
        html_data = ''
        try:
            self.logger.info(f"Calculation parameteres: {calculation_param}")
            data = asdict(calculation_param)
            response = await self.client.post(
                url='https://paper-trader.frwd.one/',
                headers=Papertrader.headers_1,
                data=data
            )
            if response.status_code == 200:
                html_data = response.text
        except Exception as exc:
            self.logger.error(f"{self.__class__.__name__} _get_calculation_html_page {exc}")
        finally:
            return html_data

    async def _get_image_file(self, img_name: str) -> str:
        image_file_path = ''
        try:
            url = f'https://paper-trader.frwd.one/images/render-{img_name}.png'
            async with self.client.stream('GET', url=url, headers=Papertrader.headers_2) as response:
                if response.status_code == 200:
                    image_file_path = os.path.join(Papertrader.tmp_dir, f'{img_name}.png')
                    async with aiofiles.open(image_file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            await f.write(chunk)
                else:
                    self.logger.error(f"{url} Status code: {response.status_code}")
        except Exception as exc:
            image_file_path = ''
            self.logger.error(f"{self.__class__.__name__} _get_image_file {exc}")
        finally:
            return image_file_path

    async def process(self, calculation_param: Calculation) -> str:
        try:
            image_file_path = ''
            html_data = await self._get_calculation_html_page(calculation_param)
            if html_data:
                img_file_name = Papertrader.find_regex(pattern=Papertrader.img_regex, searched_string=html_data)
                if img_file_name:
                    image_file_path = await self._get_image_file(img_file_name)
                    self.logger.info(f"Image file: {image_file_path}")
        except Exception as exc:
            image_file_path = ''
            self.logger.error(f"{self.__class__.__name__} process {exc}")
        finally:
            return image_file_path
