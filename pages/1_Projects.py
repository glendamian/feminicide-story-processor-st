import altair
import streamlit as st
import pandas as pd
from dashboard import PLATFORMS
import dashboard.projects as projects
import dashboard.database.processor_db as processor_db
from Dashboard import draw_graph, story_results_graph


def draw_model_scores(project_id):
    scores = [entry.values() for entry in processor_db.project_binned_model_scores(project_id)]
    chart = pd.DataFrame(scores, columns=["scores", "number of projects"])
    chart["scores"] *= 10
    bar_chart = altair.Chart(chart).mark_bar().encode(
        x=altair.X('scores'),
        y="number of projects",
        size=altair.SizeValue(35)
    )
    st.altair_chart(bar_chart, use_container_width=True)
    return


def latest_stories(stories):
    ids = [""] + [s.stories_id for s in stories]
    story_id = st.selectbox(
        'Select story',
        (ids))
    if story_id != "":
        s = [story for story in stories_above if story.stories_id == story_id][0]
        st.markdown('ID : ' + str(s.stories_id))
        st.markdown('Source: ' + str(s.source))
        st.markdown('Published Date: ' + str(s.published_date))
        st.markdown('URL: [link](story.url)')
        st.markdown('Model Score: ' + str(s.model_score))
    return


# Projects
st.title("Projects Specific Feminicide Story Dashboard")
st.markdown("Choose a project ID from the dropdown box to show the story dashboard")
list_of_projects = projects.load_project_list(force_reload=True, download_if_missing=True)
titles = [""] + [p['title'] for p in list_of_projects]
option = st.selectbox('Select project', titles)

if option != "":
    selected = [p for p in list_of_projects if p['title'] == option][0]
    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 25px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    # Project Attributes
    st.caption("Project Attributes")
    col1, col2, col3 = st.columns(3)
    col1.metric("ID", str(selected['id']))
    st.markdown('Title : ' + str(selected['title']))
    st.markdown("Model : " + str(selected['language_model']))
    st.divider()

    # Project Statistics
    unposted_above_story_count = processor_db.unposted_above_story_count(selected['id'])
    posted_above_story_count = processor_db.posted_above_story_count(selected['id'])
    below_story_count = processor_db.below_story_count(selected['id'])
    try:
        above_threshold_pct = 100 * (unposted_above_story_count + posted_above_story_count) / below_story_count
    except ZeroDivisionError:
        above_threshold_pct = 100

    st.markdown(
        """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 25px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.caption("Statistics")
    col1, col2 = st.columns(2)
    col1.metric("Average Above Threshold Percentage", above_threshold_pct)
    col2.metric("Unposted Above Threshold Stories", unposted_above_story_count)
    col3, col4 = st.columns(2)
    col3.metric("Posted Above Threshold Stories", posted_above_story_count)
    col4.metric("Below Threshold Stories", below_story_count)
    st.divider()

    # Model Scores
    st.subheader("Model Scores")
    draw_model_scores(project_id=selected['id'])
    st.divider()

    st.subheader('Above Threshold Stories')
    # by posted day
    st.caption("Platform Stories by Posted Day")
    draw_graph(processor_db.stories_by_posted_day, selected['id'])
    st.divider()
    # History (by discovery date)
    st.subheader("History")
    st.caption("Platform Stories by Published Day")
    draw_graph(processor_db.stories_by_published_day, selected['id'])
    st.caption("Platform Stories by Discovery Day")
    draw_graph(processor_db.stories_by_processed_day, selected['id'])
    st.caption("Platform Stories by Discovery Day")
    story_results_graph(selected['id'])
    st.divider()

    # Latest Stories
    st.subheader("Latest Stories")
    st.caption("Above threshold")
    stories_above = processor_db.recent_stories(selected['id'], True)
    latest_stories(stories_above)
    for s in stories_above:
        st.markdown('ID : ' + str(s.stories_id))
        st.markdown('Source: ' + str(s.source))
        st.markdown('Published Date: ' + str(s.published_date))
        st.markdown('URL: [link](story.url)')
        st.markdown('Model Score: ' + str(s.model_score))
    st.divider()

    st.caption("Below threshold")
    stories_below = processor_db.recent_stories(selected['id'], False)
    latest_stories(stories_below)
    for s in stories_below:
        st.markdown('ID : ' + str(s.stories_id))
        st.markdown('Source: ' + str(s.source))
        st.markdown('Published Date: ' + str(s.published_date))
        st.markdown('URL: [link](story.url)')
        st.markdown('Model Score: ' + str(s.model_score))
    st.divider()

    st.title('Project Speficic Email Alert Dashboard')
    st.markdown("Choose a project ID from the dropdown box to show the email alert dashboard")
    st.divider()

    # Grouped Articles
    st.subheader('Grouped Articles')
    st.divider()

    # Raw Articles
    st.subheader('Raw Articles')
    st.divider()

