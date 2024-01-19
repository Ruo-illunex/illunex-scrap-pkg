from datetime import datetime, timedelta
from app.common.db.scraper_manager_database import ScraperManagerDatabase

scraper_mng_db = ScraperManagerDatabase()


def create_daily_message():
    yesterday = datetime.today().date() - timedelta(days=1)
    portal_stats = scraper_mng_db.get_scraping_statistics_by_portal(yesterday)

    # 메세지 포맷팅
    message_format = "📅 {} 뉴스 스크래핑 요약\n-------------------------\n{}\n-------------------------"
    messages = [f"{portal.upper()}:\n- 성공 개수: {stats['success']}\n- 실패 개수: {stats['fail']}"
                for portal, stats in portal_stats.items()]

    final_message = "\n\n".join(messages)
    final_message = message_format.format(yesterday, final_message)

    return final_message


def create_error_report_message(error_message, portal):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_format = "❌ {} 뉴스 스크래핑 에러\n-------------------------\n{}\n{}\n-------------------------"
    message = message_format.format(portal.upper(), error_message, current_time)

    return message
