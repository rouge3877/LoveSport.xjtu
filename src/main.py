# main.py

import sys
import os
import time

from venueAvailability import VenueAvailability

"""
Two threads:
    - one for get availability venue
    - one for Login, use the available venue to book
"""

def find_available_venue(date: str = None, service_id: int = 42):

    va_client = VenueAvailability(service_id=service_id)
    
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
        
    areas = va_client.areas


