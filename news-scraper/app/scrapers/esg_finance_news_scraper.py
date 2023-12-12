import asyncio
import random
import hashlib
import traceback
import types
import glob
import os

import aiohttp
from bs4 import BeautifulSoup
import pandas as pd
from trafilatura import fetch_url, bare_extraction

from app.common.core.base_news_scraper import NewsScraper
from app.models_init import EsgNews
from app.scrapers.urls import URLs
from app.scrapers.esg_finance_hub_scraper import EsgFinanceHubScraper
from app.common.core.utils import *
from app.config.settings import FILE_PATHS
from app.common.core.utils import load_yaml


class EsgfinanceNewsScraper(NewsScraper):
    """ESG FINANCE 뉴스 스크래퍼 클래스"""

    def __init__(self, scraper_name: str):
        super().__init__(scraper_name)
        self.interval_time_sleep = 7200
        esgfinance_urls = URLs(self.scraper_name)
        self.headers = esgfinance_urls.headers
        urls = esgfinance_urls.urls
        self.news_board_url = urls['news_board_url']
        self.esg_finance_hub_scraper = EsgFinanceHubScraper(scraper_name=self.scraper_name)
        self.media_name = None
        self.type1 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type1')
        self.type2 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type2')
        self.type3 = load_yaml(FILE_PATHS.get('esg_finance_media')).get('type3')
        self.media = load_yaml(FILE_PATHS.get('esg_finance_media')).get('media')
        # self.type1 = ['www.impacton.net', 'www.greened.kr', 'www.greenpostkorea.co.kr', 'www.esgeconomy.com', 'www.sporbiz.co.kr', 'news.einfomax.co.kr', 'www.dailyimpact.co.kr', 'www.straightnews.co.kr', 'www.kbanker.co.kr', 'www.econovill.com', 'www.seoulfn.com', 'www.fortunekorea.co.kr', 'www.hansbiz.co.kr', 'www.meconomynews.com', 'www.ekoreanews.co.kr', 'www.enewstoday.co.kr', 'www.dhdaily.co.kr', 'www.m-i.kr', 'www.newsworks.co.kr', 'www.seoulwire.com', 'www.ngetnews.com', 'www.energydaily.co.kr', 'www.shinailbo.co.kr', 'www.whitepaper.co.kr', 'www.insightkorea.co.kr', 'www.e2news.com', 'daily.hankooki.com', 'www.insidevina.com', 'www.electimes.com', 'www.digitaltoday.co.kr', 'www.newspost.kr', 'www.domin.co.kr', 'www.infostockdaily.co.kr', 'www.getnews.co.kr', 'www.thereport.co.kr', 'www.polinews.co.kr', 'www.ccdailynews.com', 'www.gasnews.com', 'thepublic.kr', 'www.hkbs.co.kr', 'www.lcnews.co.kr', 'www.biztribune.co.kr', 'www.consumernews.co.kr', 'www.newsfreezone.co.kr', 'www.bloter.net', 'www.goodkyung.com', 'www.newswatch.kr', 'www.businessplus.kr', 'www.choicenews.co.kr', 'www.wikileaks-kr.org', 'www.cctoday.co.kr', 'www.gukjenews.com', 'www.lecturernews.com', 'www.koit.co.kr', 'www.joongboo.com', 'www.fetimes.co.kr', 'www.ftoday.co.kr', 'www.incheonilbo.com', 'www.kpinews.co.kr', 'www.intn.co.kr', 'www.lifein.news', 'www.thekpm.com', 'www.updownnews.co.kr', 'www.sisaon.co.kr', 'it.chosun.com', 'www.safetimes.co.kr', 'www.wolyo.co.kr', 'www.newsquest.co.kr', 'www.newslock.co.kr', 'www.dailycnc.com', 'www.cstimes.com', 'www.newscj.com', 'www.kbmaeil.com', 'www.worktoday.co.kr', 'www.jeonmae.co.kr', 'www.wiseenews.com', 'www.job-post.co.kr', 'www.womancs.co.kr', 'www.womentimes.co.kr', 'www.weeklyseoul.net', 'www.smartcitytoday.co.kr', 'www.startuptoday.co.kr', 'www.speconomy.com', 'www.obsnews.co.kr', 'www.sisafocus.co.kr', 'www.kihoilbo.co.kr', 'www.ezyeconomy.com', 'www.asiaa.co.kr', 'www.efnews.co.kr', 'polinews.co.kr', 'www.foodneconomy.com', 'www.consumerwide.com', 'www.eroun.net', 'www.bizwnews.com', 'www.sejungilbo.com', 'www.4th.kr', 'www.aflnews.co.kr', 'www.shippingnewsnet.com', 'www.siminsori.com', 'www.ntoday.co.kr', 'www.1conomynews.co.kr', 'www.pennmike.com', 'www.pharmnews.com', 'www.policetv.co.kr', 'www.popcornnews.net', 'www.outsourcing.co.kr', 'www.pressm.kr', 'www.opinionnews.co.kr', 'www.rcast.co.kr', 'www.s-journal.co.kr', 'www.safetynews.co.kr', 'www.psnews.co.kr', 'www.snmnews.com', 'www.sisajournal-e.com', 'www.veritas-a.com', 'www.weeklytoday.com', 'www.ziksir.com', 'www.smedaily.co.kr', 'news.unn.net', 'www.startuptoday.kr', 'www.thedailypost.kr', 'www.thefirstmedia.net', 'www.apnews.kr', 'www.it-b.co.kr', 'www.hankooki.com', 'www.goodnews1.com', 'www.globalnewsagency.kr', 'www.ggilbo.com', 'www.kongje.or.kr', 'www.kgdm.co.kr', 'www.koreaittimes.com', 'www.koscaj.com', 'www.fntoday.co.kr', 'www.firenzedt.com', 'www.kunews.ac.kr', 'www.fintechpost.co.kr', 'www.jeonmin.co.kr', 'www.itdaily.kr', 'www.iusm.co.kr', 'www.jbnews.com', 'www.jejudomin.co.kr', 'www.jejuilbo.net', 'www.jejumaeil.net', 'www.jemin.com', 'www.industrynews.co.kr', 'www.iminju.net', 'www.headlinejeju.co.kr', 'www.iloveorganic.co.kr', 'www.ikpnews.net', 'www.kbiznews.co.kr', 'www.laborplus.co.kr', 'www.newsworker.co.kr', 'www.newscape.co.kr', 'www.newsclaim.co.kr', 'www.constimes.co.kr', 'www.newsggam.com', 'www.newsian.co.kr', 'www.coindeskkorea.com', 'www.newskr.kr', 'www.newspenguin.com', 'www.cupnews.kr', 'www.cctimes.kr', 'www.cbci.co.kr', 'www.bzeronews.com', 'www.businesskorea.co.kr', 'www.itbiznews.com', 'www.consumuch.com', 'www.latimes.kr', 'www.energy-news.co.kr', 'www.lawleader.co.kr', 'www.finomy.com', 'www.financialreview.co.kr', 'www.legaltimes.co.kr', 'www.epnc.co.kr', 'www.engdaily.com', 'www.nbnnews.co.kr', 'www.economytalk.kr', 'www.mhns.co.kr', 'www.delighti.co.kr', 'www.dailysmart.co.kr']

    def get_all_links_and_save_to_csv(self):
        """모든 링크를 가져와서 CSV 파일에 저장하는 함수"""
        try:
            self.esg_finance_hub_scraper.get_all_links_and_save_to_csv()
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = "THERE WAS AN ERROR WHILE GETTING ALL LINKS AND SAVING TO CSV.\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_all_links_and_save_to_csv", stack_trace, e)


    def preprocess_datetime(self, unprocessed_date):
        """날짜 전처리 함수
        Args:
            unprocessed_date (str): 전처리되지 않은 날짜
        Returns:
            str: 전처리된 날짜
        """
        processed_date = preprocess_datetime_iso(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_compact(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_compact_with_seperator(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_rfc2822(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_standard(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_standard_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_korean_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_datetime_period_without_seconds(unprocessed_date)
        if processed_date:
            return processed_date

        processed_date = preprocess_date_period(unprocessed_date)
        if processed_date:
            return processed_date

        try:
            raise ValueError(f"Invalid date format: {unprocessed_date}")
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE PROCESSING DATE: {unprocessed_date}"
            self.process_err_log_msg(err_message, "preprocess_datetime", stack_trace, e)
            return None


    def get_news_urls(self):
        try:
            for link in self.esg_finance_hub_scraper.get_first_page_links():
                domain = link.split('/')[2]
                if domain in self.type1:
                    self.media_name = self.type1.get(domain)
                    self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub1')
                elif domain in self.type2:
                    self.media_name = self.type2.get(domain)
                    self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub2')
                elif domain in self.type3:
                    self.media_name = self.type3.get(domain)
                    self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub3')
                elif domain in self.media:
                    self.media_name = self.media.get(domain)
                    self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name=self.media_name)
                else:
                    self.media_name = None
                    self.parsing_rules_dict = None
                yield link
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING NEWS URLS FROM {self.news_board_url}\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_news_urls", stack_trace, e)
            return None


    def get_all_news_urls(self):
        try:
            # CSV 파일 경로
            file_path = FILE_PATHS.get(f'{self.scraper_name}_links_csv')
            file_list = glob.glob(file_path)

            # CSV 파일이 존재하는 경우
            if file_list:
                file_list.sort(key=lambda x: os.path.splitext(os.path.basename(x))[0][-14:])
                latest_file = file_list[-1]
                df = pd.read_csv(latest_file)
                df.columns = ['page', 'url']
                df = df.drop_duplicates(subset=['url'], keep='first')
                for url in df['url'].tolist():
                    domain = url.split('/')[2]
                    if domain in self.type1:
                        self.media_name = self.type1.get(domain)
                        self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub1')
                    elif domain in self.type2:
                        self.media_name = self.type2.get(domain)
                        self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub2')
                    elif domain in self.type3:
                        self.media_name = self.type3.get(domain)
                        self.parsing_rules_dict = self.get_parsing_rules_dict(scraper_name='esg_finance_hub3')
                    else:
                        self.media_name = None
                        self.parsing_rules_dict = None
                    yield url
            # CSV 파일이 존재하지 않는 경우
            else:
                info_message = f"CSV FILE DOES NOT EXIST FOR {self.scraper_name}"
                self.process_info_log_msg(info_message, type="info")

                self.get_all_links_and_save_to_csv()
                return None

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE GETTING ALL NEWS URLS FROM {self.news_board_url}\nCHECK THE ESG FINANCE HUB SCRAPER LOGS FOR MORE DETAILS"
            self.process_err_log_msg(err_message, "get_all_news_urls", stack_trace, e)
            return None


    async def scrape_each_news(self, news_url):
        try:
            info_message = f"SCRAPING STARTED FOR {news_url}"
            self.process_info_log_msg(info_message, type="info")

            async with aiohttp.ClientSession() as session:
                async with session.get(news_url, headers=self.headers) as response:
                    if response.status == 200:
                        try:
                            text = await response.text()
                        except UnicodeDecodeError:
                            info_message = f"ENCODING ERROR FOR {news_url}"
                            self.process_info_log_msg(info_message, type="info")
                            text = await response.read()
                            if self.media_name in ["dt", "wsobi", "munhwa"]:
                                text = text.decode('euc-kr', 'ignore')
                            elif self.media_name in ["digitalchosun", "news1", "seoul", "newsworks"]:
                                text = text.decode('utf-8', 'ignore')
                        soup = BeautifulSoup(text, 'html.parser')
                    else:
                        err_message = f"RESPONSE STATUS: {response.status} {response.reason} FOR URL: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                        return None

            extracted_data = self.extract_news_details(
                soup,
                )

            title = extracted_data.get('title')
            content = extracted_data.get('content')
            create_date = extracted_data.get('create_date')
            image_url = extracted_data.get('image_url')
            media = extracted_data.get('media')

            # title이나 content가 없으면 다음 데이터로 넘어갑니다.
            if not title or not content:
                err_message = f"TITLE OR CONTENT IS EMPTY FOR URL: {news_url}"
                self.process_err_log_msg(err_message, "scrape_each_news", "", "")
                return None

            if self.media_name in ["dt", "metroseoul"]:
                image_url = f"https:{image_url}"

            if self.media_name in ["paxetv"]:
                create_date = create_date.split('승인')[-1].strip()

            if self.media_name in ["digitalchosun_dizzo", "dnews", "thevaluenews"]:
                create_date = create_date[5:]

            # if self.media_name == "biz_chosun":
            #     create_date = create_date.split('.')[0]
            
            # if self.media_name == "newstong":
            #     create_date = create_date.split('|')[-1].strip()
            
            if self.media_name == "metroseoul":
                create_date = create_date.split('ㅣ')[-1].strip()
            
            # if self.media_name == "mediapen":
            #     create_date = create_date.split(' | ')[0].strip()
            
            if self.media_name == "ceoscoredaily":
                image_url = f"https://www.ceoscoredaily.com{image_url}"

            if self.media_name in ["theguardian", "news_yahoo", "uk_news_yahoo", "sg_news_yahoo", "bbc", "ca_news_yahoo", "au_news_yahoo", "nz_news_yahoo"]:
                create_date = create_date.split('.')[0]
            
            # if self.media_name in ["news2day", "nongmin"]:
            #     create_date = create_date.split(' : ')[-1].strip()

            # if self.media_name == "busan":
            #     create_date = create_date.replace('[', '').replace(']', '')
            
            if self.media_name == "the bell":
                create_date = create_date.replace('공개 ', '').strip()

            # if self.media_name == "munhwa":
            #     create_date = create_date.replace('입력 ', '').strip()
            
            # if self.media_name == "news_kbs":
            #     create_date = create_date.replace('입력 ', '').replace('(', '').replace(')', '').strip()
            
            # if self.media_name == "asiatime":
            #     create_date = create_date.split('입력 ')[-1].split(' 수정')[0].strip()

            # if self.media_name == "economist":
            #     create_date = create_date.replace('[이코노미스트] 입력 ', '')
            
            # if self.media_name == "naeil":
            #     create_date = create_date.replace(' 게재', '')

            if self.media_name == "kjdaily":
                create_date = create_date[:11].replace(' ', '') + create_date[14:]
            
            if self.media_name == "jnilbo":
                create_date = create_date.split(' : ')[-1][:11].replace(' ', '') + create_date.split(' : ')[-1][14:]

            if self.media_name in ["news_mtn", "wowtv", "cnn"]:
                create_date = create_date[:-1]

            url_md5 = hashlib.md5(news_url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
            kind_id = self.category_dict.get(self.scraper_name).get("etc")

            news_data = EsgNews(
                url=news_url,
                url_md5=url_md5,
                title=title,
                content=content,
                create_date=preprocessed_create_date,
                image_url=image_url,
                portal='esg_finance',
                media=media,
                kind=kind_id,
                category="ESG",
                esg_analysis="",
                )

            return news_data

        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news", stack_trace, e)
            return None


    async def scrape_each_news_with_trafilatura(self, news_url):
        try:
            info_message = f"SCRAPING STARTED FOR {news_url} WITH TRAFILATURA"
            self.process_info_log_msg(info_message, type="info")

            media_name_dict = {
                "www.lawtimes.co.kr": "법률신문",
            }

            downloaded = fetch_url(
                news_url,
                no_ssl=True,
                )

            domain = news_url.split('/')[2]
            if domain in media_name_dict.keys():
                result = bare_extraction(downloaded)
                title = result.get('title')
                create_date = result.get('date')
                content = result.get('description')
                image_url = result.get('image')
                media = media_name_dict[domain]
            else:
                result = bare_extraction(downloaded, with_metadata=True)
                title = result.get('title')
                create_date = result.get('date')
                content = result.get('text')
                image_url = result.get('image')
                media = result.get('sitename')

            url_md5 = hashlib.md5(news_url.encode()).hexdigest()
            preprocessed_create_date = self.preprocess_datetime(create_date)
            kind_id = self.category_dict.get(self.scraper_name).get("etc")

            news_data = EsgNews(
                url=news_url,
                url_md5=url_md5,
                title=title,
                content=content,
                create_date=preprocessed_create_date,
                image_url=image_url,
                portal='esg_finance',
                media=media,
                kind=kind_id,
                category="ESG",
                esg_analysis="",
                )

            return news_data
        
        except Exception as e:
            stack_trace = traceback.format_exc()
            err_message = f"THERE WAS AN ERROR WHILE SCRAPING: {news_url}"
            self.process_err_log_msg(err_message, "scrape_each_news_with_trafilatura", stack_trace, e)
            return None


    async def scrape_news(self, get_all_news_urls=False):
        """뉴스를 스크래핑하는 함수"""
        is_loop = True
        while is_loop:
            try:
                # 세션 로그 초기화
                self.is_error = False
                self.initialize_session_log()

                # 뉴스 데이터 리스트 초기화
                self.news_data_list = []

                if get_all_news_urls:
                    news_urls = self.get_all_news_urls()
                else:
                    news_urls = self.get_news_urls()

                if not isinstance(news_urls, types.GeneratorType):
                    err_message = "GET_NEWS_URLS DOES NOT RETURN A GENERATOR. CHECK THE 'news_board_url' OR THE RETURN VALUE OF FUNCTION 'get_news_urls'"
                    self.process_err_log_msg(err_message, "scrape_news", "", "")
                    return None

                for news_url in news_urls:
                    news_data = None
                    # 에러 로그 개별 초기화
                    self.is_error = False
                    self.initialize_error_log(news_url)

                    self.session_log['total_records_processed'] += 1
                    if not self.is_already_scraped(news_url):
                        await asyncio.sleep(random.randint(1, 5))

                        if self.media_name:
                            info_message = f"SCRAPING STARTED FOR {news_url} WITH {self.media_name}"
                            self.process_info_log_msg(info_message, type="info")
                            news_data = await self.scrape_each_news(news_url)
                            # if not news_data:
                            #     info_message = f"SCRAPING STARTED FOR {news_url} WITH TRAFILATURA BECAUSE OF ERROR"
                            #     self.process_info_log_msg(info_message, type="info")
                            #     news_data = await self.scrape_each_news_with_trafilatura(news_url)
                        # elif not self.media_name:
                        #     info_message = f"SCRAPING STARTED FOR {news_url} WITH TRAFILATURA"
                        #     self.process_info_log_msg(info_message, type="info")
                        #     news_data = await self.scrape_each_news_with_trafilatura(news_url)
                    else:
                        err_message = f"NEWS ALREADY EXISTS IN DATABASE: {news_url}"
                        self.process_err_log_msg(err_message, "scrape_news", "", "")

                    # 뉴스 데이터에 에러가 있으면, 에러 로그를 append하고, 그렇지 않으면 뉴스 데이터를 리스트에 추가
                    self.check_error(news_data, news_url)

                    if get_all_news_urls:
                        # 매 100개의 뉴스마다 데이터 베이스에 저장
                        if len(self.news_data_list) == 100:
                            self.save_news_data_bulk(self.news_data_list)
                            self.news_data_list = []

                # 뉴스 데이터베이스에 한 번에 저장
                self.save_news_data_bulk(self.news_data_list)
                
                # 최종 세션 로그 저장
                self.finalize_session_log()
                success_message = f"SCRAPING COMPLETED FOR {self.scraper_name} WITH {self.session_log['total_records_processed']} RECORDS"
                self.process_info_log_msg(success_message, "scrape_news")

            except Exception as e:
                stack_trace = traceback.format_exc()
                err_message = "THERE WAS AN ERROR WHILE SCRAPING NEWS"
                self.process_err_log_msg(err_message, "scrape_news", stack_trace, e)
                await asyncio.sleep(self.retry_delay)

            finally:
                if get_all_news_urls:
                    is_loop = False
                else:
                    # 모든 스크래핑이 끝나면 일정 시간 대기
                    await asyncio.sleep(self.interval_time_sleep)


    def get_feed_entries(self):
        pass


    async def scrape_each_feed_entry(self, entry):
        pass


# ESG FINANCE 뉴스 스크래핑
async def scrape_esg_finance_news(get_all_news_urls=False):
    """ESG FINANCE 뉴스를 스크래핑하는 함수"""
    portal = "esg_finance_hub"
    esgfinance_news_scraper = EsgfinanceNewsScraper(scraper_name=portal)
    await esgfinance_news_scraper.scrape_news(get_all_news_urls=get_all_news_urls)


if __name__ == "__main__":
    asyncio.run(scrape_esg_finance_news())
