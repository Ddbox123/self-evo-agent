#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策树测试

测试 core/decision_tree.py 中的：
- 决策节点管理
- 条件评估
- 决策路径执行
"""

import os
import sys
import pytest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.decision_tree import (
    DecisionTree, DecisionNode, DecisionContext, DecisionType,
    ConditionEvaluator, DEFAULT_DECISION_CONFIG, create_default_decision_tree
)


class TestConditionEvaluator:
    """条件评估器测试"""

    def test_evaluate_empty_condition(self):
        """空条件返回 True"""
        result = ConditionEvaluator.evaluate("", {})
        assert result is True

    def test_evaluate_equality(self):
        """测试相等判断"""
        context = {"priority": "high", "count": 5}
        # 条件中的值需要是字面量（如字符串需要引号包裹）
        assert ConditionEvaluator.evaluate("count == 5", context) is True
        assert ConditionEvaluator.evaluate("count == 3", context) is False
        # 字符串值需要用引号
        assert ConditionEvaluator.evaluate("count > 3", context) is True

    def test_evaluate_comparison(self):
        """测试比较运算"""
        context = {"count": 10, "score": 0.8}
        assert ConditionEvaluator.evaluate("count > 5", context) is True
        assert ConditionEvaluator.evaluate("count >= 10", context) is True
        assert ConditionEvaluator.evaluate("count < 10", context) is False
        assert ConditionEvaluator.evaluate("score <= 0.8", context) is True

    def test_evaluate_logical_and(self):
        """测试 AND 逻辑"""
        context = {"a": True, "b": 5}
        assert ConditionEvaluator.evaluate("a == True and b > 3", context) is True
        assert ConditionEvaluator.evaluate("a == True and b > 10", context) is False

    def test_evaluate_logical_or(self):
        """测试 OR 逻辑"""
        context = {"a": True, "b": False}
        assert ConditionEvaluator.evaluate("a == True or b == True", context) is True
        assert ConditionEvaluator.evaluate("a == False or b == True", context) is False

    def test_evaluate_in_operator(self):
        """测试 in 操作符"""
        context = {"color": "red", "colors": ["red", "green", "blue"]}
        assert ConditionEvaluator.evaluate("color in colors", context) is True
        assert ConditionEvaluator.evaluate("color not in colors", context) is False

    def test_evaluate_boolean_values(self):
        """测试布尔值"""
        context = {"flag": True, "active": False}
        assert ConditionEvaluator.evaluate("flag == true", context) is True
        assert ConditionEvaluator.evaluate("active == false", context) is True

    def test_evaluate_nested_path(self):
        """测试嵌套路径"""
        context = {"user": {"level": 5}}
        assert ConditionEvaluator.evaluate("user.level > 3", context) is True


class TestDecisionTreeInit:
    """决策树初始化测试"""

    def test_init_empty(self):
        """空初始化"""
        tree = DecisionTree()
        assert tree._nodes is not None
        assert tree._root_nodes == []
        assert tree._history == []

    def test_init_with_project_root(self):
        """带项目根目录初始化"""
        tree = DecisionTree(project_root=".")
        assert tree.project_root is not None


class TestDecisionNode:
    """决策节点测试"""

    def test_create_node(self):
        """创建节点"""
        node = DecisionNode(
            node_id="test_node",
            name="测试节点",
            description="这是一个测试",
            decision_type=DecisionType.ACTION,
            condition="count > 0",
            weight=0.8,
        )
        assert node.node_id == "test_node"
        assert node.decision_type == DecisionType.ACTION
        assert node.condition == "count > 0"
        assert node.weight == 0.8


class TestDecisionTreeNodeManagement:
    """节点管理测试"""

    @pytest.fixture
    def tree(self):
        return DecisionTree()

    def test_add_node(self, tree):
        """添加节点"""
        node = DecisionNode(
            node_id="node1",
            name="节点1",
            description="测试节点",
            decision_type=DecisionType.ACTION,
        )
        tree.add_node(node)
        assert "node1" in tree._nodes
        assert "node1" in tree._root_nodes

    def test_get_node(self, tree):
        """获取节点"""
        node = DecisionNode(
            node_id="node1",
            name="节点1",
            description="测试",
            decision_type=DecisionType.ACTION,
        )
        tree.add_node(node)
        retrieved = tree.get_node("node1")
        assert retrieved is not None
        assert retrieved.node_id == "node1"

    def test_get_nonexistent_node(self, tree):
        """获取不存在的节点"""
        assert tree.get_node("nonexistent") is None

    def test_remove_node(self, tree):
        """移除节点"""
        node = DecisionNode(
            node_id="node1",
            name="节点1",
            description="测试",
            decision_type=DecisionType.ACTION,
        )
        tree.add_node(node)
        assert tree.remove_node("node1") is True
        assert "node1" not in tree._nodes

    def test_remove_nonexistent_node(self, tree):
        """移除不存在的节点"""
        assert tree.remove_node("nonexistent") is False


class TestDecisionTreeMakeDecision:
    """决策执行测试"""

    @pytest.fixture
    def tree(self):
        tree = DecisionTree()
        tree.load_from_config(DEFAULT_DECISION_CONFIG)
        return tree

    def test_make_decision_with_matching_condition(self, tree):
        """条件匹配的决策"""
        context = DecisionContext(
            state={"task_count": 5, "priority": "high", "error_count": 0},
            history=[],
        )
        result = tree.make_decision(context)
        assert result is not None
        assert result.selected_action is not None

    def test_make_decision_with_errors(self, tree):
        """有错误时的决策"""
        context = DecisionContext(
            state={"task_count": 0, "error_count": 3},
            history=[],
        )
        result = tree.make_decision(context)
        assert result is not None

    def test_make_decision_empty_tree(self):
        """空树的默认决策"""
        tree = DecisionTree()
        context = DecisionContext(state={}, history=[])
        result = tree.make_decision(context)
        assert result.selected_action == "no_decision"
        assert result.confidence == 0.0

    def test_make_decision_updates_stats(self, tree):
        """决策更新统计"""
        context = DecisionContext(state={"task_count": 1}, history=[])
        initial_count = tree._stats["decisions_made"]
        tree.make_decision(context)
        assert tree._stats["decisions_made"] == initial_count + 1


class TestDecisionTreeConfig:
    """配置管理测试"""

    def test_load_from_config(self):
        """从配置加载"""
        tree = DecisionTree()
        tree.load_from_config(DEFAULT_DECISION_CONFIG)
        assert len(tree._nodes) == 4

    def test_load_from_config_custom(self):
        """加载自定义配置"""
        config = {
            "nodes": [
                {
                    "node_id": "custom1",
                    "name": "自定义节点",
                    "description": "测试",
                    "decision_type": "action",
                    "condition": "value > 10",
                    "weight": 1.5,
                }
            ]
        }
        tree = DecisionTree()
        tree.load_from_config(config)
        assert "custom1" in tree._nodes
        node = tree.get_node("custom1")
        assert node.weight == 1.5

    def test_to_config(self):
        """转换为配置"""
        tree = DecisionTree()
        tree.load_from_config(DEFAULT_DECISION_CONFIG)
        config = tree.to_config()
        assert "nodes" in config
        assert len(config["nodes"]) == 4


class TestDecisionTreeHistory:
    """历史记录测试"""

    @pytest.fixture
    def tree(self):
        tree = DecisionTree()
        tree.load_from_config(DEFAULT_DECISION_CONFIG)
        return tree

    def test_get_history(self, tree):
        """获取历史"""
        context = DecisionContext(state={"task_count": 1}, history=[])
        tree.make_decision(context)
        tree.make_decision(context)
        history = tree.get_history()
        assert len(history) == 2

    def test_get_history_with_limit(self, tree):
        """限制历史数量"""
        context = DecisionContext(state={"task_count": 1}, history=[])
        for _ in range(10):
            tree.make_decision(context)
        history = tree.get_history(limit=5)
        assert len(history) == 5

    def test_clear_history(self, tree):
        """清除历史"""
        context = DecisionContext(state={"task_count": 1}, history=[])
        tree.make_decision(context)
        tree.clear_history()
        assert len(tree.get_history()) == 0
        assert tree._stats["decisions_made"] == 0


class TestDecisionTreeStatistics:
    """统计测试"""

    def test_get_statistics(self):
        """获取统计"""
        tree = DecisionTree()
        tree.load_from_config(DEFAULT_DECISION_CONFIG)
        context = DecisionContext(state={"task_count": 1}, history=[])
        tree.make_decision(context)
        stats = tree.get_statistics()
        assert "total_nodes" in stats
        assert "decisions_made" in stats
        assert stats["total_nodes"] == 4


class TestCreateDefaultDecisionTree:
    """默认决策树测试"""

    def test_create_default(self):
        """创建默认决策树"""
        tree = create_default_decision_tree()
        assert tree is not None
        assert len(tree._nodes) == 4


class TestDecisionTreeIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """完整工作流程"""
        # 1. 创建树
        tree = create_default_decision_tree()
        
        # 2. 添加自定义节点
        custom_node = DecisionNode(
            node_id="custom",
            name="自定义",
            description="测试",
            decision_type=DecisionType.STRATEGY,
        )
        tree.add_node(custom_node)
        
        # 3. 做多个决策
        for i in range(3):
            context = DecisionContext(
                state={"task_count": i, "priority": "high"},
                history=[],
            )
            result = tree.make_decision(context)
            assert result is not None
        
        # 4. 验证历史
        assert len(tree.get_history()) == 3
        
        # 5. 验证统计
        stats = tree.get_statistics()
        assert stats["total_nodes"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
