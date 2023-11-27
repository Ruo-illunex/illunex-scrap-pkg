class Messages:
    """
    다양한 종류의 메시지를 관리하는 클래스
    """
    

    # 에러 메시지 관리
    @staticmethod
    def error_message(message, function_name, stack_trace="", exception=""):
        """에러 메시지를 출력하는 함수"""
        message = f"\n\t[ERROR] {message}\n\t{function_name}\n\t{stack_trace}\n\t{exception}"
        return message


    # 성공 메시지 관리
    @staticmethod
    def success_message(message):
        """성공 메시지를 출력하는 함수"""
        message = f"\n\t[SUCCESS] {message}"
        return message


    # 정보 메시지 관리
    @staticmethod
    def info_message(message):
        """정보 메시지를 출력하는 함수"""
        message = f"\n\t[INFO] {message}"
        return message


    # 경고 메시지 관리
    @staticmethod
    def warning_message(message):
        """경고 메시지를 출력하는 함수"""
        message = f"\n\t[WARNING] {message}"
        return message
