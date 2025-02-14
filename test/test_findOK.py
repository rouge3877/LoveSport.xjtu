import sys
import os
import time

# 将 ../src（即 LoveSport/src）路径添加到 sys.path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from venueAvailability import VenueAvailability


def test_findOK(date: str = None):
    va_client = VenueAvailability(service_id=42)
    
    # 获取原始数据
    va_client.get_availability(date)

    # 筛选可用场地
    num = va_client.filter_available_areas()

        
    if num > 0:
        print(f"可用场地数量: {num}")
        # 打印结构化JSON
        # va_client.print_availability_report_json()
        # 打印可读报告
        va_client.print_availability_report()

if __name__ == "__main__":

    
    today = time.strftime("%Y-%m-%d", time.localtime())
    print(f"Today is {today}")
    test_findOK(today)
