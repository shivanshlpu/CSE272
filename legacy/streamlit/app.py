"""Interactive multilingual sentiment monitoring dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.ingestion import generate_synthetic_benchmark, fetch_unified_stream
from src.dataset_loader import load_corpus
from src.preprocessing import preprocess
from src.llm_engine import analyze, add_weights, weighted_sentiment, sentiment_timeline, generate_shift_summary
from src.llm_bertopic import fit_topics, representative_posts

st.set_page_config(page_title='Signal · Multilingual Intelligence', page_icon='◉', layout='wide')
st.title('Signal · Multilingual Intelligence')
st.caption('CSEAIML2026-P17 · Public conversation, sentiment and emerging themes')
with st.sidebar:
    st.header('Monitor a conversation')
    source = st.selectbox('Data source', ['Synthetic Bot Benchmark','Hugging Face Large Corpus','Live Reddit + YouTube + RSS'])
    keyword = st.text_input('Brand, policy or topic', 'UPI')
    n = st.slider('Organic sample size', 100, 50000, 300, step=100)
    languages = st.multiselect('Languages', ['en','hi','hi-en'], default=['en','hi','hi-en'])
    bot_filter = st.toggle('Bot Filter', value=True)
    provider = st.selectbox('LLM provider', ['auto','groq','ollama'], help='auto uses the deterministic offline heuristic.')
    semantic = st.checkbox('Multilingual semantic model', help='Downloads multilingual MiniLM on first use; otherwise uses lexical TF-IDF/SVD.')
    frequency = st.selectbox('Time buckets', ['D','h'])
    run = st.button('Run analysis', type='primary')

@st.cache_data(show_spinner=False, ttl=300)
def pipeline(source, keyword, n, provider, semantic):
    raw = generate_synthetic_benchmark(n) if source.startswith('Synthetic') else load_corpus(n) if source.startswith('Hugging') else fetch_unified_stream(keyword,n)
    messages = raw.attrs.get('messages', ['Synthetic benchmark: all posts and engagement are simulated.'])
    frame = fit_topics(analyze(preprocess(raw), provider), semantic, provider)
    frame.attrs['messages'] = messages
    return frame

if run:
    try:
        with st.spinner('Loading posts, isolating duplicates and analyzing discussion…'):
            st.session_state['analysis'] = pipeline(source,keyword,n,provider,semantic)
            st.session_state['analysis_provider'] = provider
    except Exception as exc:
        st.error(f'Analysis could not complete ({type(exc).__name__}). Reduce the sample size or use synthetic mode.')
if 'analysis' not in st.session_state:
    st.info('Select a source and run analysis. No API keys are needed for the synthetic demonstration.')
    st.stop()
base = st.session_state['analysis']
for message in base.attrs.get('messages', []):
    st.info(message)
if (base.inference_mode == 'heuristic').any():
    st.warning('Offline heuristic sentiment is active for some posts. These are not LLM predictions; benchmark targets are not guaranteed.')
st.caption(base.attrs.get('topic_mode',''))
if base.attrs.get('topic_warning'):
    st.warning(base.attrs['topic_warning'])
df = add_weights(base[base.lang.isin(languages)], bot_filter)
if df.empty:
    st.info('No posts match the selected languages.')
    st.stop()
a,b,c,d = st.columns(4)
naive, weighted = float(df.polarity.mean()), weighted_sentiment(df)
a.metric('Total Posts Analyzed', f'{len(df):,}')
b.metric('Standard Naive Sentiment', f'{naive:+.3f}')
c.metric('Impact-Weighted Organic Sentiment' if bot_filter else 'Impact-Weighted All Posts', f'{weighted:+.3f}', f'{weighted-naive:+.3f} vs naive')
d.metric('Bots Blocked / Sarcasm Caught', f'{int(df.is_bot.sum()) if bot_filter else 0} / {int(df.is_sarcastic.sum())}')
timeline = sentiment_timeline(df,frequency)
for row in timeline[timeline['shift']].itertuples():
    window = df[pd.to_datetime(df.timestamp).dt.floor(frequency) == row.timestamp]
    st.warning(f'Why Sentiment Shifted · {row.timestamp}: '+generate_shift_summary(window, st.session_state['analysis_provider']))
fig = go.Figure()
fig.add_trace(go.Scatter(x=timeline.timestamp,y=timeline.naive,name='Naive sentiment',line=dict(color='#9ca3af',dash='dot')))
fig.add_trace(go.Scatter(x=timeline.timestamp,y=timeline.weighted,name='Impact-weighted sentiment',line=dict(color='#be123c')))
shifts = timeline[timeline['shift']]
fig.add_trace(go.Scatter(x=shifts.timestamp,y=shifts.weighted,mode='markers',name='Detected drop',marker=dict(size=12,color='#f59e0b')))
fig.update_layout(title='How public mood changes',yaxis_range=[-1,1],height=380)
st.plotly_chart(fig,use_container_width=True)
left,right = st.columns(2)
with left:
    st.subheader('Discussion landscape')
    st.plotly_chart(px.scatter(df, x='umap_x',y='umap_y',color='topic_title',size='effective_weight',hover_data=['text','lang'],size_max=25),use_container_width=True)
with right:
    st.subheader('Regional sentiment')
    geo = df.dropna(subset=['lat','lon'])
    if geo.empty:
        st.info('No explicit Indian location mentions. Unknown locations are not invented.')
    else:
        regions = pd.DataFrame([dict(state=s,lat=g.lat.iloc[0],lon=g.lon.iloc[0],sentiment=weighted_sentiment(g),posts=len(g)) for s,g in geo.groupby('state')])
        chart = px.scatter_geo(regions,lat='lat',lon='lon',color='sentiment',size='posts',hover_name='state',color_continuous_scale='RdYlGn',range_color=[-1,1])
        chart.update_geos(fitbounds='locations')
        st.plotly_chart(chart,use_container_width=True)
st.subheader('Posts driving each trend')
for topic, posts in representative_posts(df).items():
    group = df[df.topic_id == topic]
    with st.expander(f'{posts.topic_title.iloc[0]} · {len(group)} posts · sentiment {weighted_sentiment(group):+.2f}'):
        for col, (_, post) in zip(st.columns(3),posts.iterrows()):
            with col:
                st.write(post.text)
                st.caption(f'{post.author} · {post.lang} · reach {post.author_followers:,}')
                st.write(f'{post.emotion} · '+('Sarcasm' if post.is_sarcastic else post.label))
                st.caption(post.reason)
with st.expander('Throughput and provenance'):
    st.json(base.attrs.get('telemetry',{}))
st.download_button('Download analyzed posts',df.to_csv(index=False).encode('utf-8'),'analyzed_posts.csv','text/csv')
