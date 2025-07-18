"""
SubGraph Service for LANGGRAPH subgraph management.

@author malou
@since 2025-01-08
Note: 子图服务，专注于子图的管理和单独调用
"""

import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List

from app.workflows.subgraph.base import SubGraph, State
from app.workflows.subgraph.split_query import SplitQueryStep, split_query_graph
from app.workflows.subgraph.generate_sql import GenerateSQLStep, generate_sql_graph
from app.workflows.subgraph.fetch_data import FetchDataStep, fetch_data_graph

from app.utils.logger import logger


class SubGraphService:
    """
    SubGraph service for managing and executing subgraphs.
    
    Note: 子图服务，管理和执行各种子图
    """
    
    def __init__(self):
        """
        Note: 初始化子图服务
        """
        self.subgraphs: Dict[str, SubGraph] = {}
        self.compiled_graphs: Dict[str, Any] = {}  # 缓存编译后的图
        
        # 注册默认子图
        self._register_default_subgraphs()
        
        logger.info("SubGraphService initialized")
    
    def _register_default_subgraphs(self):
        """
        Note: 注册默认的子图
        """
        try:
            # 注册子图实例和预编译的图
            self.register_subgraph("split_query", SplitQueryStep())
            self.register_subgraph("generate_sql", GenerateSQLStep())
            self.register_subgraph("fetch_data", FetchDataStep())
            
            # 注册预编译的图实例
            self.compiled_graphs["split_query"] = split_query_graph
            self.compiled_graphs["generate_sql"] = generate_sql_graph
            self.compiled_graphs["fetch_data"] = fetch_data_graph
            
            logger.info("Default subgraphs and compiled graphs registered successfully")
            
        except ImportError as e:
            logger.warning(f"Failed to import some subgraph modules: {e}")
        except Exception as e:
            logger.error(f"Failed to register default subgraphs: {e}")
    
    
    def register_subgraph(self, name: str, subgraph: SubGraph) -> None:
        """
        @param name str 子图名称
        @param subgraph SubGraph 子图实例
        Note: 注册子图
        """
        self.subgraphs[name] = subgraph
        logger.info(f"Registered subgraph: {name}")
    
    
    async def execute_subgraph(self, name: str, state: State) -> State:
        """
        @param name str 子图名称
        @param state State 输入状态
        @return State 执行结果
        @throws KeyError 子图不存在
        Note: 执行指定子图
        """
        if name not in self.subgraphs:
            raise KeyError(f"SubGraph '{name}' not found")
        
        # 优先使用预编译的图实例
        if name in self.compiled_graphs:
            compiled_graph = self.compiled_graphs[name]
        else:
            # 如果没有预编译的图，则动态编译
            subgraph = self.subgraphs[name]
            compiled_graph = subgraph.compile()
            self.compiled_graphs[name] = compiled_graph
        
        result = await compiled_graph.ainvoke(state) # type: ignore
        
        logger.info(f"Executed subgraph: {name}")
        return result

    async def execute_subgraph_stream(
        self, 
        name: str, 
        state: State
    ) -> AsyncGenerator[State, None]:
        """
        @param name str 子图名称
        @param state State 输入状态
        @return AsyncGenerator[State, None] 流式执行结果
        @throws KeyError 子图不存在
        Note: 流式执行指定子图
        """
        if name not in self.subgraphs:
            raise KeyError(f"SubGraph '{name}' not found")
        
        # 优先使用预编译的图实例
        if name in self.compiled_graphs:
            compiled_graph = self.compiled_graphs[name]
        else:
            # 如果没有预编译的图，则动态编译
            subgraph = self.subgraphs[name]
            compiled_graph = subgraph.compile()
            self.compiled_graphs[name] = compiled_graph
        
        # 注意：这里需要根据具体的子图实现来调整流式执行
        # 目前大多数子图可能不支持流式执行，这里提供一个基础实现
        result = await compiled_graph.ainvoke(state) # type: ignore
        yield result
    
    def list_subgraphs(self) -> List[str]:
        """
        @return List[str] 子图名称列表
        Note: 获取所有已注册的子图名称
        """
        return list(self.subgraphs.keys())
    
    def get_subgraph(self, name: str) -> Optional[SubGraph]:
        """
        @param name str 子图名称
        @return Optional[SubGraph] 子图实例
        Note: 获取指定子图
        """
        return self.subgraphs.get(name)
    

# 全局子图服务实例
subgraph_service = SubGraphService()

