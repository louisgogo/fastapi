#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SQL语句提取工具
用于从LLM返回的各种格式文本中提取完整的SQL语句
"""

import re
from typing import Optional, List, Dict, Any
import json

def extract_json_from_text(text: str) -> list:
    """从文本中提取JSON数组"""
    try:
        # 尝试直接解析
        return json.loads(text)
    except json.JSONDecodeError:
        # 如果直接解析失败，尝试提取JSON部分
        # 查找可能的JSON数组模式
        patterns = [
            r'\[.*?\]',  # 匹配方括号内的内容
            r'\{.*?\}',  # 匹配花括号内的内容
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    result = json.loads(match)
                    if isinstance(result, list):
                        return result
                except json.JSONDecodeError:
                    continue
        
        # 如果还是失败，返回默认值
        print(f"无法解析JSON，原始文本: {text}")
        return ["步骤1: 分析用户需求", "步骤2: 生成SQL查询"]

def extract_sql_from_text(text: str) -> Optional[str]:
    """
    从文本中提取SQL语句
    
    Args:
        text: 包含SQL的文本
        
    Returns:
        提取出的SQL语句，如果没有找到则返回None
    """
    if not text:
        return None
    
    # 清理文本
    text = text.strip()
    
    # 1. 尝试提取代码块中的SQL
    # 匹配 ```sql ... ``` 或 ```psql ... ``` 格式
    code_block_patterns = [
        r'```sql\s*(.*?)\s*```',
        r'```psql\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',  # 通用代码块
    ]
    
    for pattern in code_block_patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        if matches:
            sql = matches[0].strip()
            if is_valid_sql(sql):
                return sql
    
    # 2. 尝试提取以SELECT、INSERT、UPDATE、DELETE开头的语句
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']
    
    # 按行分割，查找包含SQL关键字的行
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(line.upper().startswith(keyword) for keyword in sql_keywords):
            # 检查是否以分号结尾
            if line.endswith(';'):
                return line
            else:
                # 如果不以分号结尾，尝试找到完整语句
                return extract_complete_sql(line, text)
    
    # 3. 如果文本本身就是SQL语句
    if is_valid_sql(text):
        return text
    
    # 4. 尝试从文本中提取看起来像SQL的部分
    # 匹配包含FROM、WHERE等关键字的文本
    sql_pattern = r'\b(SELECT\s+.*?(?:FROM|WHERE|GROUP BY|ORDER BY|LIMIT|OFFSET).*?)(?:;|$)'
    matches = re.findall(sql_pattern, text, re.DOTALL | re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        if not sql.endswith(';'):
            sql += ';'
        return sql
    
    return None

def extract_complete_sql(partial_sql: str, full_text: str) -> str:
    """
    从部分SQL语句和完整文本中提取完整的SQL语句
    """
    # 找到部分SQL在完整文本中的位置
    start_pos = full_text.find(partial_sql)
    if start_pos == -1:
        return partial_sql
    
    # 从该位置开始查找完整的SQL语句
    remaining_text = full_text[start_pos:]
    
    # 查找语句结束的位置（分号或换行）
    end_pos = remaining_text.find(';')
    if end_pos != -1:
        return remaining_text[:end_pos + 1].strip()
    
    # 如果没有分号，尝试找到下一个换行符
    lines = remaining_text.split('\n')
    if len(lines) > 1:
        return lines[0].strip()
    
    return partial_sql

def is_valid_sql(text: str) -> bool:
    """
    检查文本是否是有效的SQL语句
    """
    if not text:
        return False
    
    # 检查是否包含SQL关键字
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'FROM', 'WHERE']
    text_upper = text.upper()
    
    # 至少包含一个SQL关键字
    has_keyword = any(keyword in text_upper for keyword in sql_keywords)
    
    # 检查基本语法结构
    has_basic_structure = (
        ('SELECT' in text_upper and 'FROM' in text_upper) or
        ('INSERT' in text_upper) or
        ('UPDATE' in text_upper and 'SET' in text_upper) or
        ('DELETE' in text_upper and 'FROM' in text_upper)
    )
    
    return has_keyword and has_basic_structure

def clean_sql(sql: str) -> str:
    """
    清理SQL语句，移除多余的空格和换行符
    """
    if not sql:
        return ""
    
    # 移除多余的空白字符
    sql = re.sub(r'\s+', ' ', sql.strip())
    
    # 确保以分号结尾
    if not sql.endswith(';'):
        sql += ';'
    
    return sql

def extract_multiple_sql_statements(text: str) -> List[str]:
    """
    从文本中提取多个SQL语句
    """
    if not text:
        return []
    
    # 按分号分割
    statements = text.split(';')
    sql_statements = []
    
    for statement in statements:
        statement = statement.strip()
        if statement and is_valid_sql(statement):
            sql_statements.append(clean_sql(statement))
    
    return sql_statements