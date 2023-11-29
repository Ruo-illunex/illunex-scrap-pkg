class URLs:

    def __init__(self, portal) -> None:
        self.portal = portal
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            }
        self.urls = {}
        self.retrieve_news_urls()
    

    def retrieve_news_urls(self) -> dict:
        """뉴스 URL을 가져오는 함수"""
        if self.portal == 'naver':
            self.urls['news_board_url'] = self.get_naver_newsboard_url()

        elif self.portal == 'daum':
            self.urls['news_board_url'] = self.get_daum_newsboard_url()

        elif self.portal == 'zdnet':
            self.urls['news_board_url'] = self.get_zdnet_newsboard_url()
            self.urls['base_url'] = self.get_zdnet_base_url()

        elif self.portal == 'startuptoday':
            self.urls['news_board_url'] = self.get_startuptoday_newsboard_url()
            self.urls['base_url'] = self.get_startuptoday_base_url()

        elif self.portal == 'startupn':
            self.urls['news_board_url'] = self.get_startupn_newsboard_url()
            self.urls['base_url'] = self.get_startupn_base_url()

        elif self.portal == 'the bell':
            self.urls['news_board_url'] = self.get_thebell_newsboard_url()
            self.urls['base_url'] = self.get_thebell_base_url()

        elif self.portal == 'venturesquare':
            self.urls['news_board_url'] = self.get_vs_newsboard_url()

        elif self.portal == 'platum':
            self.urls['news_board_url'] = self.get_platum_newsboard_url()

        elif self.portal == 'esg_economy':
            self.urls['news_board_url_economy'] = self.get_esgeconomy_newsboard_url1()
            self.urls['news_board_url_social_and_env'] = self.get_esgeconomy_newsboard_url2()

        elif self.portal == 'greenpost_korea':
            self.urls['news_board_url'] = self.get_greenpostkorea_newsboard_url()

        else:
            raise ValueError(f"Error: {self.portal} is not a valid portal name")     


    def get_daum_newsboard_url(self):
        """다음 뉴스 카테고리별 URL을 생성하는 함수"""
        return "https://news.daum.net/breakingnews/{}"
    

    def get_naver_newsboard_url(self):
        """네이버 뉴스 카테고리별 URL을 생성하는 함수"""
        return "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1={}"
    

    def get_zdnet_newsboard_url(self):
        """ZDNet 뉴스 보드 URL을 리턴하는 함수"""
        return "https://zdnet.co.kr/news/?lstcode=0000&page=1"
    

    def get_zdnet_base_url(self):
        """ZDNet 뉴스 기사 URL을 리턴하는 함수"""
        return "https://zdnet.co.kr{}"


    def get_startuptoday_newsboard_url(self):
        """StartupToday 뉴스 보드 URL을 리턴하는 함수"""
        return "https://www.startuptoday.kr/news/articleList.html?sc_section_code=S1N45&view_type=sm"
    

    def get_startuptoday_base_url(self):
        """StartupToday 뉴스 기사 URL을 리턴하는 함수"""
        return "https://startuptoday.co.kr{}"
    

    def get_startupn_newsboard_url(self):
        """StartupN 뉴스 보드 URL을 리턴하는 함수"""
        return "https://www.startupn.kr/news/articleList.html?sc_section_code=S1N2&view_type=sm"
    

    def get_startupn_base_url(self):
        """StartupN 뉴스 기사 URL을 리턴하는 함수"""
        return "https://www.startupn.kr{}"
    

    def get_thebell_newsboard_url(self):
        """TheBell 뉴스 보드 URL을 리턴하는 함수"""
        return "https://www.thebell.co.kr/free/content/Article.asp?svccode=00"
    

    def get_thebell_base_url(self):
        """TheBell 뉴스 기사 URL을 리턴하는 함수"""
        return "https://www.thebell.co.kr/free/content/{}"
    

    def get_vs_newsboard_url(self):
        """Venture Square 뉴스 피드 URL을 리턴하는 함수"""
        return "https://www.venturesquare.net/category/news-contents/feed"

    def get_platum_newsboard_url(self):
        """Platum 뉴스 피드 URL을 리턴하는 함수"""
        return "https://platum.kr/feed"

    def get_esgeconomy_newsboard_url1(self):
        """ESG Economy rss URL을 리턴하는 함수"""
        return "https://www.esgeconomy.com/rss/S1N1.xml"

    def get_esgeconomy_newsboard_url2(self):
        """ESG Economy rss URL을 리턴하는 함수"""
        return "https://www.esgeconomy.com/rss/S1N2.xml"

    def get_greenpostkorea_newsboard_url(self):
        """Greenpostkorea rss URL을 리턴하는 함수"""
        return "https://www.greenpostkorea.co.kr/rss/allArticle.xml"
