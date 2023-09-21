import datetime as dt
from typing import List, Dict
import logging
import streamlit as st
import psycopg2
import psycopg2.extras

from dashboard import ALERTS_DB_URI

logger = logging.getLogger(__name__)


@st.cache_resource  # so it only run once
def init_connection():
    return psycopg2.connect(ALERTS_DB_URI)


db_conn = init_connection()


def _run_query(query: str) -> List[Dict]:
    dict_cursor = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    dict_cursor.execute(query)
    results = dict_cursor.fetchall()
    return results


def recent_articles(project_id: int, limit: int = 5) -> List:
    """
    UI: show a list of the most recent stories we have processed
    :param project_id:
    :param limit:
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=7)
    sql = '''
        SELECT * FROM articles WHERE
            project_id={} AND publish_date >= '{}'::DATE
            ORDER BY RANDOM() DESC LIMIT {}
    '''.format(project_id, earliest_date, limit)
    return _run_query(sql)


def _articles_by_date_col(column_name: str, project_id: int = None, limit: int = 30) -> List:
    """
    UI: How many stories are published on a particular date
    :param column_name
    :param project_id:
    :param limit:
    :return:
    """
    earliest_date = dt.date.today() - dt.timedelta(days=limit)
    clauses = []
    if project_id is not None:
        clauses.append("(project_id={})".format(project_id))
    query = "select "+column_name+"::date as day, count(1) as articles from articles " \
            "where ("+column_name+" is not Null) and ("+column_name+" >= '{}'::DATE) AND {} " \
            "group by 1 order by 1 DESC".format(earliest_date, " AND ".join(clauses))
    return _run_query(query)


def articles_by_published_day(project_id: int = None, limit: int = 30) -> List:
    return _articles_by_date_col('published_date', project_id, limit)


def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0]['count']