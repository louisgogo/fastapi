"""
异步化实现完整性验证脚本

@author malou
@since 2025-01-08
Note: 验证AIProject异步化改造的完整性和正确性
"""

import asyncio
import inspect
import sys
from pathlib import Path
from typing import List, Dict, Any, Callable
import importlib.util


class AsyncImplementationVerifier:
    """异步实现验证器"""
    
    def __init__(self):
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": []
        }
    
    def add_result(self, category: str, test_name: str, status: str, message: str = ""):
        """添加测试结果"""
        self.results["details"].append({
            "category": category,
            "test": test_name,
            "status": status,
            "message": message
        })
        
        if status == "PASS":
            self.results["passed"] += 1
        elif status == "FAIL":
            self.results["failed"] += 1
        else:
            self.results["warnings"] += 1
    
    def print_result(self, category: str, test_name: str, status: str, message: str = ""):
        """打印测试结果"""
        status_icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[?]")
        print(f"  {status_icon} {test_name}: {message}")
        self.add_result(category, test_name, status, message)
    
    def verify_api_routes_async(self) -> None:
        """验证API路由异步化"""
        print("\n[检查] 验证API路由异步化...")
        
        api_files = [
            "app/api/v1/users.py",
            "app/api/v1/health.py",
            "app/api/v1/agents.py",
            "app/api/v1/api_keys.py",
            "app/api/v1/feedback.py",
            "app/api/v1/logs.py"
        ]
        
        for api_file in api_files:
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否有异步路由函数
                async_functions = content.count("async def ")
                sync_functions = content.count("def ") - async_functions
                
                if "get_async_db" in content and "AsyncSession" in content:
                    self.print_result("API路由", api_file, "PASS", 
                                    f"已异步化 - {async_functions}个异步函数")
                elif sync_functions > 0 and "router.get" in content:
                    self.print_result("API路由", api_file, "WARN", 
                                    f"可能有同步函数 - {sync_functions}个")
                else:
                    self.print_result("API路由", api_file, "PASS", "配置文件或非路由文件")
                    
            except FileNotFoundError:
                self.print_result("API路由", api_file, "WARN", "文件不存在")
            except Exception as e:
                self.print_result("API路由", api_file, "FAIL", f"检查失败: {str(e)}")
    
    def verify_services_async(self) -> None:
        """验证服务层异步化"""
        print("\n[检查] 验证服务层异步化...")
        
        service_files = [
            "app/services/user_service.py",
            "app/services/agent_service.py",
            "app/services/api_key_service.py",
            "app/services/feedback_service.py",
            "app/services/ollama_service.py"
        ]
        
        for service_file in service_files:
            try:
                with open(service_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查异步标识
                if "AsyncSession" in content and "await " in content:
                    async_methods = content.count("async def ")
                    self.print_result("服务层", service_file, "PASS", 
                                    f"已异步化 - {async_methods}个异步方法")
                elif "session: Session" in content:
                    self.print_result("服务层", service_file, "FAIL", "仍使用同步Session")
                else:
                    self.print_result("服务层", service_file, "WARN", "需要手动检查")
                    
            except FileNotFoundError:
                self.print_result("服务层", service_file, "WARN", "文件不存在")
            except Exception as e:
                self.print_result("服务层", service_file, "FAIL", f"检查失败: {str(e)}")
    
    def verify_database_connections(self) -> None:
        """验证数据库连接配置"""
        print("\n[检查] 验证数据库连接配置...")
        
        try:
            with open("app/database/connection.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查异步数据库配置
            if "create_async_engine" in content:
                self.print_result("数据库", "异步引擎", "PASS", "已配置异步数据库引擎")
            else:
                self.print_result("数据库", "异步引擎", "FAIL", "缺少异步数据库引擎")
            
            if "AsyncSessionLocal" in content:
                self.print_result("数据库", "异步会话", "PASS", "已配置异步会话工厂")
            else:
                self.print_result("数据库", "异步会话", "FAIL", "缺少异步会话工厂")
            
            if "get_async_db" in content:
                self.print_result("数据库", "异步依赖", "PASS", "已提供异步数据库依赖")
            else:
                self.print_result("数据库", "异步依赖", "FAIL", "缺少异步数据库依赖")
                
        except FileNotFoundError:
            self.print_result("数据库", "连接配置", "FAIL", "数据库连接文件不存在")
        except Exception as e:
            self.print_result("数据库", "连接配置", "FAIL", f"检查失败: {str(e)}")
    
    def verify_external_clients(self) -> None:
        """验证外部客户端异步化"""
        print("\n[检查] 验证外部客户端异步化...")
        
        try:
            with open("app/services/ollama_service.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "httpx.AsyncClient" in content:
                self.print_result("外部客户端", "OLLAMA服务", "PASS", "使用异步HTTP客户端")
            elif "requests." in content:
                self.print_result("外部客户端", "OLLAMA服务", "FAIL", "仍使用同步requests")
            else:
                self.print_result("外部客户端", "OLLAMA服务", "WARN", "需要手动检查")
                
        except FileNotFoundError:
            self.print_result("外部客户端", "OLLAMA服务", "WARN", "文件不存在")
        except Exception as e:
            self.print_result("外部客户端", "OLLAMA服务", "FAIL", f"检查失败: {str(e)}")
    
    def verify_config_async_support(self) -> None:
        """验证配置文件异步支持"""
        print("\n[检查] 验证配置文件异步支持...")
        
        try:
            with open("app/core/config.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "ASYNC_DATABASE_URL" in content:
                self.print_result("配置", "异步数据库URL", "PASS", "已配置异步数据库URL")
            else:
                self.print_result("配置", "异步数据库URL", "FAIL", "缺少异步数据库URL配置")
            
            if "DATABASE_POOL_SIZE" in content:
                self.print_result("配置", "连接池配置", "PASS", "已配置数据库连接池")
            else:
                self.print_result("配置", "连接池配置", "WARN", "可能缺少连接池配置")
                
        except FileNotFoundError:
            self.print_result("配置", "配置文件", "FAIL", "配置文件不存在")
        except Exception as e:
            self.print_result("配置", "配置文件", "FAIL", f"检查失败: {str(e)}")
    
    def verify_test_async_support(self) -> None:
        """验证测试异步支持"""
        print("\n[检查] 验证测试异步支持...")
        
        try:
            with open("tests/conftest.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "async_sessionmaker" in content:
                self.print_result("测试", "异步测试会话", "PASS", "已配置异步测试会话")
            else:
                self.print_result("测试", "异步测试会话", "WARN", "可能缺少异步测试配置")
            
            if "AsyncSession" in content:
                self.print_result("测试", "异步依赖", "PASS", "测试支持异步数据库")
            else:
                self.print_result("测试", "异步依赖", "WARN", "测试可能仍使用同步数据库")
                
        except FileNotFoundError:
            self.print_result("测试", "测试配置", "WARN", "测试配置文件不存在")
        except Exception as e:
            self.print_result("测试", "测试配置", "FAIL", f"检查失败: {str(e)}")
    
    def check_remaining_sync_patterns(self) -> None:
        """检查剩余的同步模式"""
        print("\n[检查] 检查剩余的同步模式...")
        
        # 需要检查的同步模式
        sync_patterns = [
            ("requests.", "同步HTTP请求"),
            ("session: Session", "同步数据库会话"),
            ("get_db()", "同步数据库依赖"),
            ("def create_", "同步创建函数"),
            ("def get_", "同步获取函数"),
            ("def update_", "同步更新函数"),
            ("def delete_", "同步删除函数")
        ]
        
        files_to_check = [
            "app/api/v1/users.py",
            "app/api/v1/health.py", 
            "app/api/v1/agents.py",
            "app/api/v1/api_keys.py",
            "app/api/v1/feedback.py",
            "app/api/v1/logs.py",
            "app/services/user_service.py",
            "app/services/agent_service.py",
            "app/services/api_key_service.py", 
            "app/services/feedback_service.py"
        ]
        
        total_issues = 0
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                issues = []
                for pattern, description in sync_patterns:
                    if pattern in content:
                        # 排除注释和字符串中的匹配
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern in line and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                                issues.append(f"第{i}行: {description}")
                
                if issues:
                    total_issues += len(issues)
                    self.print_result("同步模式检查", file_path, "WARN", 
                                    f"发现{len(issues)}个可能的同步模式")
                    for issue in issues[:3]:  # 只显示前3个
                        print(f"    - {issue}")
                    if len(issues) > 3:
                        print(f"    - ... 还有{len(issues)-3}个问题")
                else:
                    self.print_result("同步模式检查", file_path, "PASS", "未发现同步模式")
                    
            except FileNotFoundError:
                self.print_result("同步模式检查", file_path, "WARN", "文件不存在")
            except Exception as e:
                self.print_result("同步模式检查", file_path, "FAIL", f"检查失败: {str(e)}")
        
        if total_issues == 0:
            self.print_result("同步模式检查", "总结", "PASS", "未发现明显的同步模式")
        else:
            self.print_result("同步模式检查", "总结", "WARN", f"共发现{total_issues}个可能问题")
    
    async def verify_async_functionality(self) -> None:
        """验证异步功能实际运行"""
        print("\n[检查] 验证异步功能实际运行...")
        
        try:
            # 测试异步数据库连接
            from app.database.connection import get_async_db
            
            async for session in get_async_db():
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    self.print_result("运行时验证", "异步数据库连接", "PASS", "连接正常")
                else:
                    self.print_result("运行时验证", "异步数据库连接", "FAIL", "查询结果异常")
                break
                
        except Exception as e:
            self.print_result("运行时验证", "异步数据库连接", "FAIL", f"连接失败: {str(e)}")
        
        try:
            # 测试异步OLLAMA服务
            from app.services.ollama_service import OllamaService
            
            ollama_service = OllamaService()
            health = await ollama_service.check_health()
            await ollama_service.close()
            
            if health:
                self.print_result("运行时验证", "OLLAMA异步服务", "PASS", "服务正常")
            else:
                self.print_result("运行时验证", "OLLAMA异步服务", "WARN", "服务不可用")
                
        except Exception as e:
            self.print_result("运行时验证", "OLLAMA异步服务", "FAIL", f"测试失败: {str(e)}")
    
    def print_summary(self) -> None:
        """打印验证总结"""
        print("\n" + "="*60)
        print("[统计] 异步化验证总结")
        print("="*60)
        
        total = self.results["passed"] + self.results["failed"] + self.results["warnings"]
        
        print(f"[通过] 通过: {self.results['passed']}")
        print(f"[失败] 失败: {self.results['failed']}")
        print(f"[警告]  警告: {self.results['warnings']}")
        print(f"[详情] 总计: {total}")
        
        if self.results["failed"] == 0:
            print("\n[成功] 恭喜！异步化改造基本完成！")
            if self.results["warnings"] > 0:
                print("[警告]  请注意检查警告项目，进行进一步优化。")
        else:
            print(f"\n[失败] 发现{self.results['failed']}个严重问题，需要修复。")
        
        # 按类别汇总
        print("\n[详情] 详细结果按类别:")
        categories = {}
        for detail in self.results["details"]:
            cat = detail["category"]
            if cat not in categories:
                categories[cat] = {"PASS": 0, "FAIL": 0, "WARN": 0}
            categories[cat][detail["status"]] += 1
        
        for category, counts in categories.items():
            total_cat = sum(counts.values())
            pass_rate = (counts["PASS"] / total_cat * 100) if total_cat > 0 else 0
            print(f"  {category}: {counts['PASS']}/{total_cat} 通过 ({pass_rate:.1f}%)")
        
        print("\n[建议] 建议下一步操作:")
        if self.results["failed"] > 0:
            print("1. 修复失败的检查项")
            print("2. 重新运行验证脚本")
        if self.results["warnings"] > 0:
            print("3. 检查警告项目，考虑优化")
        print("4. 更新测试代码支持异步")
        print("5. 运行完整的测试套件验证功能")


async def main():
    """主函数"""
    print("AIProject 异步化实现验证")
    print("="*60)
    
    verifier = AsyncImplementationVerifier()
    
    # 执行各项验证
    verifier.verify_api_routes_async()
    verifier.verify_services_async()
    verifier.verify_database_connections()
    verifier.verify_external_clients()
    verifier.verify_config_async_support()
    verifier.verify_test_async_support()
    verifier.check_remaining_sync_patterns()
    
    # 运行时验证（可能失败，取决于环境）
    await verifier.verify_async_functionality()
    
    # 打印总结
    verifier.print_summary()
    
    return 0 if verifier.results["failed"] == 0 else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 