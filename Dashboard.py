import altair
import streamlit as st
import pandas as pd
from dashboard import PLATFORMS
import dashboard.projects as projects
import dashboard.database.processor_db as processor_db


def draw_graph(func, project_id=None):
    df_list = []
    for p in PLATFORMS:
        results = func(project_id=project_id, platform=p, above_threshold=False)
        df = pd.DataFrame(results)
        df['platform'] = p
        df_list.append(df)

    chart = pd.concat(df_list)
    bar_chart = altair.Chart(chart).mark_bar().encode(
        x=altair.X('day', axis=altair.Axis(format='%m-%d')),
        y="stories",
        color="platform",
        size=altair.SizeValue(5),
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return


def story_results_graph(project_id=None):
    a = processor_db.stories_by_processed_day(project_id=project_id, above_threshold=True)
    b = processor_db.stories_by_processed_day(project_id=project_id, above_threshold=False)
    df_list = []
    a = pd.DataFrame(a)
    a['platform'] = 'above'
    b = pd.DataFrame(b)
    b['platform'] = 'below'
    df_list.append(a)
    df_list.append(b)
    chart = pd.concat(df_list)
    bar_chart = altair.Chart(chart).mark_bar().encode(
        x=altair.X('day', axis=altair.Axis(format='%m-%d')),
        y="stories",
        color="platform",
        size=altair.SizeValue(5)
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return

st.title('Feminicides Story Dashboard')
st.markdown('Investigate stories moving through the feminicides detection pipeline')
st.divider()

st.subheader('Above Threshold Stories (by date sent to main server)')
# by posted day
st.caption("Platform Stories by Posted Day")
draw_graph(processor_db.stories_by_posted_day)
st.divider()
# History (by discovery date)
st.subheader("History (by discovery date)")
st.caption("Platform Stories by Published Day")
draw_graph(processor_db.stories_by_published_day)
st.caption("Platform Stories by Discovery Day")
draw_graph(processor_db.stories_by_processed_day)
st.caption("Platform Stories by Discovery Day")
story_results_graph()
st.divider()

st.title('Project Speficic Email Alert Dashboard')
st.markdown("Investigate stories moving through the feminicides detection pipeline")
st.divider()

# Grouped Articles
st.subheader('Grouped Articles')
st.divider()

# Raw Articles
st.subheader('Raw Articles')
st.divider()
