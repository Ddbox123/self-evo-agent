#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息总线测试

测试 core/message_bus.py 的功能
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import (
    MessageBus,
    Message,
    MessagePriority,
    MessageFilter,
    Subscription,
    get_message_bus,
    reset_message_bus,
)


class TestMessagePriority:
    """消息优先级测试"""

    def test_all_priorities(self):
        """测试所有优先级"""
        assert MessagePriority.LOW.value == "low"
        assert MessagePriority.NORMAL.value == "normal"
        assert MessagePriority.HIGH.value == "high"
        assert MessagePriority.CRITICAL.value == "critical"


class TestMessage:
    """消息测试"""

    def test_message_creation(self):
        """测试创建消息"""
        msg = Message(
            topic="test.topic",
            data={"key": "value"},
        )
        assert msg.topic == "test.topic"
        assert msg.data["key"] == "value"
        assert msg.priority == MessagePriority.NORMAL
        assert msg.message_id is not None

    def test_message_with_priority(self):
        """测试带优先级的消息"""
        msg = Message(
            topic="test.topic",
            data="test",
            priority=MessagePriority.HIGH,
        )
        assert msg.priority == MessagePriority.HIGH


class TestMessageFilter:
    """消息过滤器测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        assert MessageFilter.match("a.b.c", "a.b.c") is True
        assert MessageFilter.match("a.b.c", "a.b.d") is False

    def test_single_wildcard(self):
        """测试单层级通配符"""
        assert MessageFilter.match("a.b.c", "a.*.c") is True
        assert MessageFilter.match("a.x.c", "a.*.c") is True
        assert MessageFilter.match("a.b.c", "a.*.d") is False

    def test_double_wildcard(self):
        """测试多层级通配符"""
        assert MessageFilter.match("a.b.c.d", "a.**") is True
        assert MessageFilter.match("x.y.z", "a.**") is False

    def test_mixed_wildcard(self):
        """测试混合通配符"""
        assert MessageFilter.match("agent.task.start", "agent.*.start") is True
        assert MessageFilter.match("agent.task.start", "agent.**.start") is True


class TestSubscription:
    """订阅测试"""

    def test_subscription_creation(self):
        """测试创建订阅"""
        def handler(msg):
            pass

        sub = Subscription(
            topic="test.topic",
            handler=handler,
            subscriber="test_subscriber",
        )
        assert sub.topic == "test.topic"
        assert sub.subscriber == "test_subscriber"
        assert sub.async_handler is False


class TestMessageBus:
    """消息总线测试"""

    def test_init(self):
        """测试初始化"""
        reset_message_bus()
        bus = MessageBus()
        assert bus.persist_messages is False
        assert len(bus.get_topics()) == 0

    def test_subscribe(self):
        """测试订阅"""
        reset_message_bus()
        bus = MessageBus()

        def handler(msg):
            pass

        sub = bus.subscribe("test.topic", handler, "tester")
        assert sub.topic == "test.topic"
        assert sub.subscriber == "tester"

    def test_unsubscribe(self):
        """测试取消订阅"""
        reset_message_bus()
        bus = MessageBus()

        def handler(msg):
            pass

        bus.subscribe("test.topic", handler, "tester")
        result = bus.unsubscribe("test.topic", handler)
        assert result is True

    def test_unsubscribe_all(self):
        """测试取消所有订阅"""
        reset_message_bus()
        bus = MessageBus()

        def handler1(msg):
            pass

        def handler2(msg):
            pass

        bus.subscribe("test1", handler1, "tester")
        bus.subscribe("test2", handler2, "tester")
        count = bus.unsubscribe_all("tester")
        assert count == 2

    def test_publish_sync(self):
        """测试同步发布"""
        reset_message_bus()
        bus = MessageBus()

        received = []

        def handler(msg):
            received.append(msg.data)

        bus.subscribe("test.topic", handler)
        result = bus.publish("test.topic", {"value": 123})
        assert result is True
        assert len(received) == 1
        assert received[0]["value"] == 123

    def test_publish_no_subscribers(self):
        """测试发布到无订阅主题"""
        reset_message_bus()
        bus = MessageBus()
        result = bus.publish("nonexistent.topic", "data")
        assert result is True  # 仍然成功发布

    def test_get_subscriptions(self):
        """测试获取订阅列表"""
        reset_message_bus()
        bus = MessageBus()

        def handler1(msg):
            pass

        def handler2(msg):
            pass

        bus.subscribe("test1", handler1, "sub1")
        bus.subscribe("test2", handler2, "sub2")

        subs = bus.get_subscriptions()
        assert len(subs) == 2

    def test_get_stats(self):
        """测试获取统计"""
        reset_message_bus()
        bus = MessageBus()

        def handler(msg):
            pass

        bus.subscribe("test", handler)
        bus.publish("test", "data")

        stats = bus.get_stats()
        assert stats["messages_sent"] == 1
        assert stats["subscriptions_count"] >= 1

    def test_clear_stats(self):
        """测试清除统计"""
        reset_message_bus()
        bus = MessageBus()
        bus.publish("test", "data")
        bus.clear_stats()
        stats = bus.get_stats()
        assert stats["messages_sent"] == 0

    def test_get_topics(self):
        """测试获取主题列表"""
        reset_message_bus()
        bus = MessageBus()

        def handler(msg):
            pass

        bus.subscribe("topic1", handler)
        bus.subscribe("topic2", handler)

        topics = bus.get_topics()
        assert "topic1" in topics
        assert "topic2" in topics

    def test_wildcard_subscription(self):
        """测试通配符订阅"""
        reset_message_bus()
        bus = MessageBus()

        received = []

        def handler(msg):
            received.append(msg.topic)

        bus.subscribe("agent.*.task", handler)
        bus.publish("agent.core.task", "data1")
        bus.publish("agent.shell.task", "data2")
        bus.publish("other.topic", "data3")

        assert len(received) == 2
        assert "agent.core.task" in received
        assert "agent.shell.task" in received


class TestSingleton:
    """单例测试"""

    def test_get_message_bus(self):
        """测试获取单例"""
        reset_message_bus()
        bus1 = get_message_bus()
        bus2 = get_message_bus()
        assert bus1 is bus2
