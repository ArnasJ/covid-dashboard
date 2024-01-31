from flask import Flask, jsonify
import pandas as pd
import snowflake.connector
from flask_caching import Cache

app = Flask(__name__)

@app.route("/")
def hello():
    return "This is Snowflake data API!"


cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

def get_connection():
    return snowflake.connector.connect(
        user='',
        password='',
        account='',
        warehouse='COMPUTE_WH',
        database='covid_data',
        schema='covid_schema'
    )

@cache.memoize(timeout=60*60*24)
def get_covid_cases():
    conn = get_connection()
    query = """
        SELECT DATE, CASES
        FROM jhu_covid_19 
        WHERE COUNTY = 'New York City' 
        AND DATE >= '2020-02-01' 
        AND DATE < '2020-09-01'
        AND CASE_TYPE = 'Active'
        ORDER BY DATE;
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

@cache.memoize(timeout=60*60*24)
def get_aqi_data():
    conn = get_connection()
    query = """
        SELECT "Date", MAX(AQI) AS MaxAQI
        FROM us_aqi
        WHERE STATE_NAME = 'New York' 
        AND "Date" >= '2020-02-01' 
        AND "Date" < '2020-09-01'
        AND "Defining Parameter" = 'PM2.5'
        GROUP BY "Date"
        ORDER BY "Date";
    """

    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

# @cache.memoize(timeout=60*60*24)
# def get_pattern_data():
#     conn = get_connection()
#     query = """
#         SELECT *
#         FROM jhu_covid_19
#         MATCH_RECOGNIZE(
#             PARTITION BY COUNTY
#             ORDER BY DATE
#             MEASURES
#                 MATCH_NUMBER() AS match_num,
#                 CLASSIFIER() AS label
#             ONE ROW PER MATCH
#             AFTER MATCH SKIP TO NEXT ROW
#             PATTERN (STRT UP_ROW+)
#             DEFINE
#                 UP_ROW AS UP_ROW.CASES > LAG(UP_ROW.CASES, 1, 0) OVER (ORDER BY DATE)
#         ) AS mr
#         WHERE COUNTY = 'New York City'
#         AND DATE >= '2020-02-01'
#         AND DATE < '2020-09-01'
#         AND CASE_TYPE = 'Confirmed';
#     """
#     try:
#         df = pd.read_sql(query, conn)
#         return df
#     finally:
#         conn.close()

# @app.route('/pattern', methods=['GET'])
# def pattern():
#     df = get_pattern_data()
#     return jsonify(df.to_dict(orient='records'))

@app.route('/covid_cases', methods=['GET'])
def covid_cases():
    df = get_covid_cases()
    return jsonify(df.to_dict(orient='records'))

@app.route('/aqi_data', methods=['GET'])
def aqi_data():
    df = get_aqi_data()
    return jsonify(df.to_dict(orient='records'))