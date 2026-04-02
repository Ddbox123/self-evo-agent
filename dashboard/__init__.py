# -*- coding: utf-8 -*-
"""
Observer Dashboard - 自我进化 Agent 监控面板

提供实时的 Web 界面来监控 Agent 的状态、日志和进化过程。
"""

from .server import DashboardServer, create_app, main

__all__ = ['DashboardServer', 'create_app', 'main']
