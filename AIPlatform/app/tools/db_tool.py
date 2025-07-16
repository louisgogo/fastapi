# -*- coding: utf-8 -*-
"""
数据库表结构导出工具
将数据库表结构信息整理为Markdown表格，适合AI上下文。
支持自动连接PostgreSQL数据库，批量导出指定schema下所有表结构。
增强：自动获取外键字段的取值范围（即外键表的所有唯一值），并在markdown表格中以"外键范围"一列展示。

作者：malou
创建时间：2024-12-19
"""
import psycopg2
import asyncio
import asyncpg
from typing import Dict, Any, List, Optional
from app.core.config import get_settings

settings = get_settings()

db_config = {
    'host': settings.PSQL_DB_HOST,
    'port': settings.PSQL_DB_PORT,
    'dbname': settings.PSQL_DB_NAME,
    'user': settings.PSQL_DB_USER,
    'password': settings.PSQL_DB_PASSWORD,
}
asyncpg_config = {
    'host': db_config['host'],
    'port': db_config['port'],
    'database': db_config['dbname'],  # asyncpg 使用 'database' 而不是 'dbname'
    'user': db_config['user'],
    'password': db_config['password'],
}

def db_table_to_markdown(table_name: str, columns: List[Dict[str, Any]]) -> str:
    """
    将数据库表结构信息整理为Markdown表格。
    
    Args:
        table_name: 表名
        columns: 字段信息列表，每个元素为dict，包含column_name, data_type, column_comment, foreign_table, foreign_column, foreign_range等
        
    Returns:
        str: markdown字符串
    """
    header = "| 字段名 | 类型 | 注释 | 外键表 | 外键字段 | 外键范围 |\n|--------|------|------|--------|----------|----------|"
    rows = []
    for col in columns:
        rows.append(
            f"| {col.get('column_name','')} | {col.get('data_type','')} | {col.get('column_comment','') or ''} | {col.get('foreign_table','') or ''} | {col.get('foreign_column','') or ''} | {col.get('foreign_range','') or ''} |"
        )
    markdown = f"### 表：{table_name}\n\n{header}\n" + "\n".join(rows)
    return markdown

async def validate_sql_query(query: str):
    """
    验证 SQL 语句是否合法.
    
    Args:
        query: SQL查询语句
        
    Returns:
        Dict: {"valid": bool, "message": str}
    """
    if not query or not query.strip():
        return {"valid": False, "message": "SQL query is required"}
    
    try:
        conn = await asyncpg.connect(**asyncpg_config)
        try:
            # 使用 EXPLAIN 命令验证 SQL 语法
            explain_query = f"EXPLAIN {query.strip()}"
            await conn.execute(explain_query)
            # 如果 EXPLAIN 命令成功执行，说明 SQL 语法正确
            return {"valid": True, "message": "SQL query is valid"}
        except Exception as e:
            # 如果 EXPLAIN 命令执行失败，说明 SQL 语法错误
            return {"valid": False, "message": f"SQL query is invalid: {str(e)}"}
        finally:
            await conn.close()
    except Exception as e:
        # 数据库连接失败
        return {"valid": False, "message": f"Database connection failed: {str(e)}"}


async def execute_sql_query(query: str):
    """
    执行 SQL 查询语句并返回结果.
    
    Args:
        query: SQL查询语句
        
    Returns:
        Dict: {
            "success": bool,
            "data": List[Dict],  # 查询结果数据
            "columns": List[str],  # 列名列表
            "row_count": int,  # 结果行数
            "error": str  # 错误信息（如果有）
        }
    """
    if not query or not query.strip():
        return {
            "success": False,
            "error": "SQL query is required",
            "data": [],
            "columns": [],
            "row_count": 0
        }
    
    try:
        conn = await asyncpg.connect(**asyncpg_config)
        try:
            # 执行查询
            result = await conn.fetch(query.strip())
            
            # 如果有结果，提取列名和数据
            if result:
                # 获取列名
                columns = list(result[0].keys()) if result else []
                
                # 将记录转换为字典列表
                data = [dict(record) for record in result]
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "error": None
                }
            else:
                # 空结果集
                return {
                    "success": True,
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                    "error": None
                }
                
        except Exception as e:
            # SQL执行失败
            return {
                "success": False,
                "error": f"SQL execution failed: {str(e)}",
                "data": [],
                "columns": [],
                "row_count": 0
            }
        finally:
            await conn.close()
            
    except Exception as e:
        # 数据库连接失败
        return {
            "success": False,
            "error": f"Database connection failed: {str(e)}",
            "data": [],
            "columns": [],
            "row_count": 0
        }


def get_unique_lvl(schema_name: str = 'public') -> str:
    """获取一二三级事业群名称并生成markdown格式"""
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    try:
        # 执行三个查询
        cur.execute("SELECT distinct(prim_org) FROM dim_org_struc")
        prim_orgs = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT distinct(sec_org) FROM dim_org_struc")
        sec_orgs = [row[0] for row in cur.fetchall()]
        cur.execute("SELECT distinct(third_org) FROM dim_org_struc")
        third_orgs = [row[0] for row in cur.fetchall()]
        
        # 用逗号连接各个列表
        prim_orgs_str = ', '.join(prim_orgs)
        sec_orgs_str = ', '.join(sec_orgs)
        third_orgs_str = ', '.join(third_orgs)
        
        # 生成markdown格式
        markdown_content = f"""# 组织架构信息

## prim_org:一级事业群
{prim_orgs_str}

## sec_org:二级事业群
{sec_orgs_str}

## third_org:三级事业群
{third_orgs_str}

## unique_org:唯一层级：由prim_org+"-"+sec_org+"-"+third_org组成
"""
        return markdown_content
        
    except Exception as e:
        print(f"获取一二三级事业群名称失败: {e}")
        return f"# 组织架构信息\n\n获取失败: {e}"
    finally:
        cur.close()
        conn.close()

class DatabaseSchemaTool():
    """数据库表结构导出工具类"""
    
    def execute(self, schema_name: str = 'public', table_filter: Optional[str] = None, max_fk_values: int = 30, **kwargs) -> Dict[str, Any]:
        """
        同步执行数据库表结构导出
        
        Args:
            schema_name: schema名，默认为'public'
            table_filter: 可选，表名过滤（字符串或None）
            max_fk_values: 外键范围最多展示多少个值，默认30
            **kwargs: 其他参数
            
        Returns:
            Dict包含导出结果和元信息
        """
        try:
            markdown_content = self._export_schema_to_markdown_sync(schema_name, table_filter, max_fk_values)
            
            return {
                "success": True,
                "markdown_content": markdown_content,
                "schema_name": schema_name,
                "table_filter": table_filter,
                "max_fk_values": max_fk_values,
                "export_method": "sync"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"导出过程中发生错误: {str(e)}",
                "schema_name": schema_name,
                "table_filter": table_filter,
                "export_method": "sync"
            }
    
    async def execute_async(self, schema_name: str = 'public', table_filter: Optional[str] = None, max_fk_values: int = 30, **kwargs) -> Dict[str, Any]:
        """
        异步执行数据库表结构导出
        
        Args:
            schema_name: schema名，默认为'public'
            table_filter: 可选，表名过滤（字符串或None）
            max_fk_values: 外键范围最多展示多少个值，默认30
            **kwargs: 其他参数
            
        Returns:
            Dict包含导出结果和元信息
        """
        try:
            markdown_content = await self._export_schema_to_markdown_async(schema_name, table_filter, max_fk_values)
            
            return {
                "success": True,
                "markdown_content": markdown_content,
                "schema_name": schema_name,
                "table_filter": table_filter,
                "max_fk_values": max_fk_values,
                "export_method": "async"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"导出过程中发生错误: {str(e)}",
                "schema_name": schema_name,
                "table_filter": table_filter,
                "export_method": "async"
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具参数schema"""
        return {
            "type": "object",
            "properties": {
                "schema_name": {
                    "type": "string",
                    "description": "数据库schema名称",
                    "default": "public"
                },
                "table_filter": {
                    "type": "string",
                    "description": "表名过滤，只导出指定表的结构",
                    "default": None
                },
                "max_fk_values": {
                    "type": "integer",
                    "description": "外键范围最多展示多少个值",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": []
        }
    
    def _export_schema_to_markdown_sync(self, schema_name: str = 'public', table_filter: Optional[str] = None, max_fk_values: int = 30) -> str:
        """
        同步导出数据库表结构为markdown
        
        Args:
            schema_name: schema名
            table_filter: 可选，表名过滤
            max_fk_values: 外键范围最多展示多少个值
            
        Returns:
            str: markdown字符串
        """
        
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        try:
            # 查所有表名
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type='BASE TABLE'
                ORDER BY table_name;
            """, (schema_name,))
            tables = [row[0] for row in cur.fetchall()]
            
            if table_filter:
                if isinstance(table_filter, str):
                    tables = [t for t in tables if t == table_filter]

            
            result = []
            for table in tables:
                cur.execute("""
                    SELECT
                        c.column_name,
                        c.data_type,
                        pgd.description AS column_comment,
                        tc.constraint_type,
                        ccu.table_name AS foreign_table,
                        ccu.column_name AS foreign_column
                    FROM
                        information_schema.columns c
                    LEFT JOIN
                        pg_catalog.pg_statio_all_tables AS st
                        ON c.table_schema = st.schemaname AND c.table_name = st.relname
                    LEFT JOIN
                        pg_catalog.pg_description pgd
                        ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                    LEFT JOIN
                        information_schema.key_column_usage kcu
                        ON c.table_name = kcu.table_name
                        AND c.column_name = kcu.column_name
                        AND c.table_schema = kcu.table_schema
                    LEFT JOIN
                        information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                        AND tc.constraint_type = 'FOREIGN KEY'
                    LEFT JOIN
                        information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                        AND tc.table_schema = ccu.table_schema
                    WHERE
                        c.table_schema = %s AND c.table_name = %s
                    ORDER BY
                        c.ordinal_position;
                """, (schema_name, table))
                
                columns = []
                for row in cur.fetchall():
                    col = {
                        'column_name': row[0],
                        'data_type': row[1],
                        'column_comment': row[2],
                        'constraint_type': row[3],
                        'foreign_table': row[4],
                        'foreign_column': row[5],
                        'foreign_range': ''
                    }
                    
                    # 如果是外键，自动查外键表的所有唯一值
                    if col['foreign_table'] and col['foreign_column']:
                        try:
                            fk_sql = f"SELECT DISTINCT {col['foreign_column']} FROM {schema_name}.\"{col['foreign_table']}\" LIMIT {max_fk_values+1};"
                            cur.execute(fk_sql)
                            fk_values = [str(r[0]) for r in cur.fetchall() if r[0] is not None]
                            if len(fk_values) > max_fk_values:
                                col['foreign_range'] = ', '.join(fk_values[:max_fk_values]) + ' ...'
                            else:
                                col['foreign_range'] = ', '.join(fk_values)
                        except Exception as e:
                            col['foreign_range'] = f"(获取失败:{e})"
                    
                    columns.append(col)
                
                result.append(db_table_to_markdown(table, columns))
            
            return '\n\n'.join(result)
            
        finally:
            cur.close()
            conn.close()
    
    async def _export_schema_to_markdown_async(self, schema_name: str = 'public', table_filter: Optional[str] = None, max_fk_values: int = 30) -> str:
        """
        异步导出数据库表结构为markdown
        
        Args:
            schema_name: schema名
            table_filter: 可选，表名过滤
            max_fk_values: 外键范围最多展示多少个值
            
        Returns:
            str: markdown字符串
        """
        
        conn = await asyncpg.connect(**asyncpg_config)
        
        try:
            # 查所有表名
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = $1 AND table_type='BASE TABLE'
                ORDER BY table_name;
            """, schema_name)
            
            table_names = [row['table_name'] for row in tables]
            
            if table_filter:
                if isinstance(table_filter, str):
                    table_names = [t for t in table_names if t == table_filter]
                else:
                    table_names = [t for t in table_names if t in table_filter]
            
            result = []
            for table in table_names:
                columns_data = await conn.fetch("""
                    SELECT
                        c.column_name,
                        c.data_type,
                        pgd.description AS column_comment,
                        tc.constraint_type,
                        ccu.table_name AS foreign_table,
                        ccu.column_name AS foreign_column
                    FROM
                        information_schema.columns c
                    LEFT JOIN
                        pg_catalog.pg_statio_all_tables AS st
                        ON c.table_schema = st.schemaname AND c.table_name = st.relname
                    LEFT JOIN
                        pg_catalog.pg_description pgd
                        ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                    LEFT JOIN
                        information_schema.key_column_usage kcu
                        ON c.table_name = kcu.table_name
                        AND c.column_name = kcu.column_name
                        AND c.table_schema = kcu.table_schema
                    LEFT JOIN
                        information_schema.table_constraints tc
                        ON kcu.constraint_name = tc.constraint_name
                        AND kcu.table_schema = tc.table_schema
                        AND tc.constraint_type = 'FOREIGN KEY'
                    LEFT JOIN
                        information_schema.constraint_column_usage ccu
                        ON tc.constraint_name = ccu.constraint_name
                        AND tc.table_schema = ccu.table_schema
                    WHERE
                        c.table_schema = $1 AND c.table_name = $2
                    ORDER BY
                        c.ordinal_position;
                """, schema_name, table)
                
                columns = []
                for row in columns_data:
                    col = {
                        'column_name': row['column_name'],
                        'data_type': row['data_type'],
                        'column_comment': row['column_comment'],
                        'constraint_type': row['constraint_type'],
                        'foreign_table': row['foreign_table'],
                        'foreign_column': row['foreign_column'],
                        'foreign_range': ''
                    }
                    
                    # 如果是外键，自动查外键表的所有唯一值
                    if col['foreign_table'] and col['foreign_column']:
                        try:
                            fk_sql = f"SELECT DISTINCT {col['foreign_column']} FROM {schema_name}.\"{col['foreign_table']}\" LIMIT {max_fk_values+1};"
                            fk_values_data = await conn.fetch(fk_sql)
                            fk_values = [str(r[col['foreign_column']]) for r in fk_values_data if r[col['foreign_column']] is not None]
                            if len(fk_values) > max_fk_values:
                                col['foreign_range'] = ', '.join(fk_values[:max_fk_values]) + ' ...'
                            else:
                                col['foreign_range'] = ', '.join(fk_values)
                        except Exception as e:
                            col['foreign_range'] = f"(获取失败:{e})"
                    
                    columns.append(col)
                
                result.append(db_table_to_markdown(table, columns))
            
            return '\n\n'.join(result)
            
        finally:
            await conn.close()

# 示例用法
async def main():
    """示例用法"""
    tool = DatabaseSchemaTool()
    result = tool.execute(table_filter="fact_expense")
    print(result)
    print(get_unique_lvl())
    result=await validate_sql_query("SELECT * FROM fact_expense")
    print(result)

if __name__ == "__main__":
    asyncio.run(main()) 