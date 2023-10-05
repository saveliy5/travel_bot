import sqlite3
import pandas as pd

# Создание или подключение к базе данных
conn = sqlite3.connect('travel_bot.db')
cursor = conn.cursor()


def sqlite_lower(value_):
    return value_.lower()


conn.create_function("LOWER", 1, sqlite_lower)

sql_query_all = """
SELECT 
count(distinct user_id) as count_unique_users,
count(*) as count_mes 
FROM message_logs
"""

sql_query_count_mes_by_users = """
SELECT 
user_id,
count(*) as count_mes 
FROM message_logs
group by 1
order by 2 desc
"""

sql_query_count_mes_by_dates = """
SELECT 
strftime('%Y-%m-%d', timestamp) as date,
count(*) as count_mes 
FROM message_logs
group by 1
order by 1
"""

sql_query_dau = """
SELECT 
strftime('%Y-%m-%d', timestamp) as date,
count(distinct user_id) as dau
FROM message_logs
group by 1
order by 1
"""

sql_query_messages = """
SELECT 
*
FROM message_logs
where user_id <> 269503586
order by 1,2,3
"""

sql_query_bad = """
SELECT 
*
FROM message_logs
where message = 'Запрос содержит опасные команды'
order by 1,2,3
"""

sql_query_unknown_towns = """
SELECT 
 log.*
FROM message_logs log
left join (
    select distinct
    city
    from cities_info
) c
on LOWER(log.message) = LOWER(c.city)
where c.city is null
and log.message <> 'Другой'
and log.message <> 'Запрос содержит опасные команды'
and LOWER(log.message) not in ('питер', 'санкт петербург', 'санкт питербург') 
order by 1,2,3
"""

sql_query_types_dates_mes = """
with type_mes as (
SELECT 
 log.*,
 case  
      when  log.message = 'Другой' Then 'Кнопка другой'
      when  log.message = 'Запрос содержит опасные команды' Then 'Запрос содержит опасные команды'
      when  c.city is not null Then 'Известный город'
      else 'Неизвестный город'
 end as type
FROM message_logs log
left join (
    select distinct
    city
    from cities_info
) c
on LOWER(log.message) = LOWER(c.city)
)
select 
strftime('%Y-%m-%d', timestamp) as date,
type,
count(*) as count
from type_mes
group by 1,2
order by 1,2
"""

sql_query_types_mes = """
with type_mes as (
SELECT 
 log.*,
 case  
      when  log.message = 'Другой' Then 'Кнопка другой'
      when  log.message = 'Запрос содержит опасные команды' Then 'Запрос содержит опасные команды'
      when  c.city is not null Then 'Известный город'
      else 'Неизвестный город'
 end as type
FROM message_logs log
left join (
    select distinct
    city
    from cities_info
) c
on LOWER(log.message) = LOWER(c.city)
)
select 
type,
count(*) as count
from type_mes
group by 1
order by 1
"""

# Используйте метод read_sql_query для создания DataFrame из результатов запроса
df_count_mes_by_users = pd.read_sql_query(sql_query_count_mes_by_users, conn)
df_count_mes_by_dates = pd.read_sql_query(sql_query_count_mes_by_dates, conn)
df_dau = pd.read_sql_query(sql_query_dau, conn)
df_messages = pd.read_sql_query(sql_query_messages, conn)
df_bad = pd.read_sql_query(sql_query_bad, conn)
df_unknown_towns = pd.read_sql_query(sql_query_unknown_towns, conn)
df_types_dates_mes = pd.read_sql_query(sql_query_types_dates_mes, conn)
df_types_mes = pd.read_sql_query(sql_query_types_mes, conn)
df_all = pd.read_sql_query(sql_query_all, conn)

conn.close()

# Теперь df содержит данные из вашей таблицы SQLite
print('За все время')
print(df_all, end='\n\n')

print('DAU')
print(df_dau, end='\n\n')

print('Количество сообщений по датам')
print(df_count_mes_by_dates, end='\n\n')

print('Количество сообщений по юзерам')
print(df_count_mes_by_users, end='\n\n')

print('Количество сообщений по типам и датам')
print(df_types_dates_mes, end='\n\n')

print('Количество сообщений по типам')
print(df_types_mes, end='\n\n')

print('Непонятные города')
print(df_unknown_towns, end='\n\n')

print('Сообщения не мои')
print(df_messages, end='\n\n')

print('Попытки взлома')
print(df_bad)
