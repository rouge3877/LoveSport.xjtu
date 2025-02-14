"""
场馆可用性查询模块

该模块提供结构化方式从指定HTTP服务获取并处理场馆可用区域信息。
封装了请求处理、数据解析、排序和可用性检查功能，便于其他模块调用。

主要类：
    VenueAvailability - 处理请求和数据的核心类

主要功能：
    - 动态生成请求参数
    - 自动处理SSL警告
    - 结构化数据解析
    - 智能场地排序
    - 结果缓存与新鲜度控制
    - 丰富的可扩展性选项
"""

import requests
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass

from config import VenueAvailabilityConfig
from config import VenueAreaStruct

# 禁用SSL警告（因目标使用HTTP协议）
requests.packages.urllib3.disable_warnings()

class VenueAvailability:
    """
    场馆可用性客户端
    
    使用示例：
    >>> client = VenueAvailability(service_id=42)
    >>> areas = client.get_availability(target_date="2025-02-12")
    """
    def __init__(
        self,
        service_id: int,
        find_type: str = "findOkArea",
        base_url: str = None,
        referer_template: str = None,
        request_timeout: int = None,
        cache_ttl: int = None
    ):
        """
        初始化客户端

        :param service_id: 服务/产品ID
        :param find_type: 查询类型（findOkArea/findLockArea）
        :param base_url: API基础路径（可留空，根据find_type自动生成）
        :param referer_template: Referer头模板
        :param request_timeout: 请求超时时间
        :param cache_ttl: 结果缓存有效期
        """
        self.service_id = service_id
        self.find_type = find_type
        
        # 自动生成base_url
        if base_url is None:
            find_key = self.find_type.lower()
            self.base_url = VenueAvailabilityConfig.URLS.get(
                find_key, 
                f"http://202.117.17.144/product/{self.find_type}.html"
            )
        else:
            self.base_url = base_url

        # 使用配置默认值
        self.referer_template = referer_template or VenueAvailabilityConfig.REFERER_TEMPLATE
        self.request_timeout = request_timeout or VenueAvailabilityConfig.DEFAULT_PARAMS['request_timeout']
        self.cache_ttl = cache_ttl or VenueAvailabilityConfig.DEFAULT_PARAMS['cache_ttl']

        self._last_fetch_time = 0

        self.areas = List[VenueAreaStruct]



    def _build_headers(self) -> Dict[str, str]:
        """构造标准请求头"""
        headers = VenueAvailabilityConfig.BASE_HEADERS.copy()
        headers['Referer'] = self.referer_template.format(service_id=self.service_id)
        return headers

    def _build_params(self, target_date: str) -> Dict[str, str]:
        """构造请求参数"""
        return {
            "s_date": target_date,
            "serviceid": self.service_id,
            "_": int(time.time() * 1000)  # 防缓存时间戳
        }

    @staticmethod
    def _parse_response(raw_data: dict) -> List[VenueAreaStruct]:
        """
        解析原始API响应
        
        :param raw_data: API返回的原始JSON数据
        :return: 结构化场地信息列表
        """
        parsed = []
        for area in raw_data.get("object", []):
            stock = area.get("stock", {})
            parsed.append(VenueAreaStruct(
                name=area.get("sname", ""),
                date=stock.get("s_date", ""),
                time_slot=stock.get("time_no", ""),
                is_available=area.get("status") == 1,
                detail_id=str(area.get("id", ""))
            ))

        parsed = VenueAvailability._sort_areas(parsed)
        # print(parsed)
        return parsed

    @staticmethod
    def _sort_areas(areas: List[VenueAreaStruct]) -> List[VenueAreaStruct]:
        """按场地名称的自然顺序排序"""
        return sorted(
            areas,
            key=lambda x: int(x.name[2:]) if x.name[2:].isdigit() else float('inf')
        )

    def get_availability(
        self,
        target_date: str,
        force_refresh: bool = False
    ) -> Optional[List[VenueAreaStruct]]:
        """
        获取指定日期的可用场地信息
        
        :param target_date: 查询日期（YYYY-MM-DD格式）
        :param force_refresh: 是否跳过缓存强制刷新
        :return: 排序后的场地信息列表（失败时返回None）
        """
        # 检查缓存有效性
        if not force_refresh and time.time() - self._last_fetch_time < self.cache_ttl:
            self.areas = self._last_response
            return self._last_response

        try:
            response = requests.get(
                url=self.base_url,
                params=self._build_params(target_date),
                headers=self._build_headers(),
                verify=False,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                parsed_data = self._parse_response(response.json())
                self._last_response = parsed_data
                self._last_fetch_time = time.time()
                self.areas = parsed_data
                return parsed_data
            
            print(f"请求失败，状态码：{response.status_code}")
            return None

        except requests.exceptions.RequestException as e:
            print(f"网络请求异常：{str(e)}")
            return None
        except json.JSONDecodeError:
            print("响应数据解析失败")
            return None
        
    def filter_available_areas(self):
        """筛选可用场地"""
        retareas = []
        for area in self.areas:
            if area.is_available == False:
                continue
            else:
                retareas.append(area)

        self.areas = retareas
        return len(retareas)
    

    def print_availability_report(self):
        """打印可读性报告"""
        print("\n=========================================\n")
        print("场地列表：")
        for idx, area in enumerate(self.areas, 1):
            status = "可用" if area.is_available else "不可用"
            print(f"  {idx:2d}. [{status}] {area.name} | 日期：{area.date} | "
                  f"时段：{area.time_slot} | ID：{area.detail_id}")
        print("\n=========================================\n")

    def print_availability_report_json(self):
        """打印JSON格式报告"""
        print(json.dumps(
            [area.__dict__ for area in self.areas],
            ensure_ascii=False,
            indent=4
        ))

if __name__ == "__main__":
    # 示例用法
    client = VenueAvailability(
        service_id=42
    )
    
    # 获取2025-02-12的场地信息
    areas = client.get_availability(target_date="2025-02-13")
    
    if areas:
        # 打印结构化JSON
        client.print_availability_report_json()
        
        # 打印可读报告
        client.print_availability_report()