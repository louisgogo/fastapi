# 数据库结构 - Schema: public


## agents

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| name | character varying(100) | 否 | - | - | Agent名称 |
| type | character varying(50) | 否 | - | - | Agent类型：nl2sql/chat/analysis等 |
| description | text | 是 | - | - | Agent功能描述 |
| config | jsonb | 是 | - | - | Agent配置信息，JSON格式 |
| status | character varying(20) | 否 | - | - | Agent状态：active/inactive/maintenance |
| version | character varying(20) | 是 | - | - | Agent版本 |
| id | uuid | 否 | - | PK | 主键ID |
| created_at | timestamp with time zone | 否 | now() | - | 创建时间 |
| updated_at | timestamp with time zone | 否 | now() | - | 更新时间 |


## api_keys

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| user_id | uuid | 否 | - | FK | 关联用户ID |
| key_value | character varying(255) | 否 | - | - | API密钥值 |
| name | character varying(100) | 是 | - | - | 密钥名称 |
| permissions | jsonb | 是 | - | - | 权限配置，JSON格式 |
| expires_at | timestamp with time zone | 是 | - | - | 过期时间 |
| is_active | boolean | 否 | - | - | 是否激活 |
| last_used_at | timestamp with time zone | 是 | - | - | 最后使用时间 |
| id | uuid | 否 | - | PK | 主键ID |
| created_at | timestamp with time zone | 否 | now() | - | 创建时间 |
| updated_at | timestamp with time zone | 否 | now() | - | 更新时间 |


## api_logs

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| user_id | uuid | 是 | - | FK | 关联用户ID |
| api_key_id | uuid | 是 | - | FK | 关联API密钥ID |
| agent_id | uuid | 是 | - | FK | 关联Agent ID |
| endpoint | character varying(255) | 否 | - | - | 请求端点路径 |
| method | character varying(10) | 否 | - | - | HTTP请求方法 |
| request_data | jsonb | 是 | - | - | 请求数据，JSON格式 |
| response_data | jsonb | 是 | - | - | 响应数据，JSON格式 |
| status_code | integer(32) | 否 | - | - | HTTP状态码 |
| execution_time | double precision(53) | 是 | - | - | 执行时间（秒） |
| client_ip | character varying(45) | 是 | - | - | 客户端IP地址 |
| user_agent | character varying(500) | 是 | - | - | 用户代理字符串 |
| id | uuid | 否 | - | PK | 主键ID |
| created_at | timestamp with time zone | 否 | now() | - | 创建时间 |
| updated_at | timestamp with time zone | 否 | now() | - | 更新时间 |


## document

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| content | text | 否 | - | - | - |
| embedding | USER-DEFINED | 否 | - | - | - |
| metadata | jsonb | 否 | - | - | - |
| timestamp | timestamp without time zone | 是 | now() | - | - |
| uuid | uuid | 否 | gen_random_uuid() | PK | - |
| doc_name | text | 否 | - | - | - |


## feedback

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| id | uuid | 否 | gen_random_uuid() | PK | - |
| created_at | timestamp with time zone | 是 | now() | - | - |
| updated_at | timestamp with time zone | 是 | now() | - | - |
| request_id | character varying(255) | 是 | - | - | - |
| user_id | uuid | 是 | - | FK | - |
| agent_id | uuid | 是 | - | FK | - |
| rating | integer(32) | 是 | - | - | - |
| feedback_text | text | 是 | - | - | - |
| is_sql_correct | boolean | 是 | - | - | - |
| suggestions | text | 是 | - | - | - |
| feedback_type | character varying(50) | 是 | - | - | - |
| priority | character varying(20) | 是 | 'medium'::character varying | - | - |
| status | character varying(20) | 是 | 'pending'::character varying | - | - |


## feedback_old

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| id | bigint(64) | 否 | nextval('feedback_id_seq'::regclass) | PK | - |
| app_id | text | 是 | - | - | - |
| app_name | text | 是 | - | - | - |
| user_id | text | 是 | - | - | - |
| workflow_run_id | text | 是 | - | - | - |
| query | text | 是 | - | - | - |
| subquery | text | 是 | - | - | - |
| answer | text | 是 | - | - | - |
| rating | text | 是 | - | - | - |


## users

| 字段名 | 数据类型 | 是否可空 | 默认值 | 约束 | 注释 |
|--------|----------|----------|--------|------|------|
| name | character varying(100) | 否 | - | - | 用户姓名 |
| email | character varying(255) | 否 | - | - | 用户邮箱 |
| department | character varying(50) | 是 | - | - | 用户部门 |
| status | character varying(20) | 否 | - | - | 用户状态：active/inactive/suspended |
| id | uuid | 否 | - | PK | 主键ID |
| created_at | timestamp with time zone | 否 | now() | - | 创建时间 |
| updated_at | timestamp with time zone | 否 | now() | - | 更新时间 |
