"""Evidence-linked aggregate analytics; no synthetic metadata or author profiling."""
from collections import Counter,defaultdict
from datetime import datetime,timezone,timedelta
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from ml.stance import LABELS

def date(value):return datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(timezone.utc)

def summarize(posts,encoder=None,at=None):
    at=at or datetime.now(timezone.utc);cutoff=at-timedelta(hours=24);previous=cutoff-timedelta(hours=24)
    current=[p for p in posts if cutoff<=date(p['published_at'])<=at]
    prior=[p for p in posts if previous<=date(p['published_at'])<cutoff]
    def stance(p):return p['review_label'] or p['stance']['label']
    def counts(items):return {label:sum(stance(p)==label for p in items) for label in LABELS}
    sentiment=Counter(p['sentiment']['label'] for p in posts)
    timeline=defaultdict(lambda:{'count':0,'positive':0,'negative':0,'neutral':0,'agree':0,'disagree':0,'no_clear_stance':0,'reviewed':0})

    post_dates=[date(p['published_at']) for p in posts]
    if post_dates:
        min_d=min(post_dates);max_d=max(post_dates);span_hours=(max_d-min_d).total_seconds()/3600
        unique_days=len(set(d.strftime('%Y-%m-%d') for d in post_dates))
        if unique_days<=2 or span_hours<=48:
            if span_hours<=4:
                def time_key(d):
                    m=(d.minute//10)*10
                    return d.strftime(f'%Y-%m-%dT%H:{m:02d}:00Z')
            else:
                def time_key(d): return d.strftime('%Y-%m-%dT%H:00:00Z')
        else:
            def time_key(d): return d.strftime('%Y-%m-%d')
    else:
        def time_key(d): return d.strftime('%Y-%m-%d')

    for p in posts:
        key=time_key(date(p['published_at']));b=timeline[key];b['count']+=1;b[p['sentiment']['label'].lower()]+=1
        b[{'Agree':'agree','Disagree':'disagree','No clear stance':'no_clear_stance'}[stance(p)]]+=1;b['reviewed']+=bool(p['review_label'])
    negative=lambda items:sum(p['sentiment']['label']=='Negative' for p in items)/len(items) if items else None
    shift=(negative(current)-negative(prior))*100 if len(current)>=10 and len(prior)>=10 else None
    themes=[]
    if len(posts)>=6 and encoder is not None:
        texts=[p['text'] for p in posts];emb=encoder.embeddings(texts)
        k=min(6,max(2,int(np.sqrt(len(posts)/3))),len(np.unique(emb,axis=0)))
        model=KMeans(n_clusters=k,random_state=42,n_init=10).fit(emb)
        try:
            vec=TfidfVectorizer(stop_words='english',ngram_range=(1,2),min_df=2,max_features=5000)
            words=vec.fit_transform(texts);names=vec.get_feature_names_out()
        except ValueError:words=None
        for c in range(k):
            ix=np.where(model.labels_==c)[0];members=[posts[i] for i in ix]
            center=emb[ix].mean(axis=0);similarity=emb[ix]@center/(np.linalg.norm(center)+1e-9)
            representative=members[int(similarity.argmax())]
            recent=sum(cutoff<=date(p['published_at'])<=at for p in members);prev=sum(previous<=date(p['published_at'])<cutoff for p in members)
            change=100*(recent/len(current)-prev/len(prior)) if len(current)>=10 and len(prior)>=10 else None
            if words is not None:
                weights=np.asarray(words[ix].mean(axis=0)).ravel();top=weights.argsort()[-4:][::-1];terms=[str(names[i]) for i in top if weights[i]>0]
            else:terms=[]
            themes.append({'id':c,'title':' · '.join(terms) or 'Mixed discussion','count':len(members),'recent':recent,'previous':prev,'share_change_pp':change,'emerging':bool(recent>=5 and change is not None and change>=5),'stance':counts(members),'representative':representative,'most_liked':max(members,key=lambda p:p['likes'])})
        themes.sort(key=lambda t:(t['emerging'],t['recent'],t['count']),reverse=True)
    insights=[]
    if not posts:insights.append('No collected comments yet. Connect YouTube and run a collection before drawing conclusions.')
    else:
        insights.append(f'{len(posts)} collected comments in this analysis; {sum(bool(p["review_label"]) for p in posts)} have analyst-reviewed stance labels.')
        if shift is not None:insights.append(f'Negative sentiment share changed by {shift:+.1f} percentage points in the latest 24 hours versus the previous 24 hours ({len(current)} vs {len(prior)} comments).')
        else:insights.append('Not enough comments in both 24-hour windows to report a supported window comparison (minimum 10 per window).')
        if themes:
            lead=themes[0];insights.append(f'Review the “{lead["title"]}” discussion: {lead["count"]} comments, {lead["recent"]} in the latest 24 hours. Open its representative comment before deciding on a response.')
    
    # 72-Hour Predictive Trend Forecasting & Crisis Velocity
    velocity = float(shift) if shift is not None else 0.0
    total_valid = len(posts)
    current_disagree = counts(posts).get('Disagree', 0)
    current_agree = counts(posts).get('Agree', 0)
    disagree_pct = round((current_disagree / total_valid * 100), 1) if total_valid else 0.0
    agree_pct = round((current_agree / total_valid * 100), 1) if total_valid else 0.0

    daily_drift = velocity if abs(velocity) > 0.1 else 0.0
    f24 = round(min(100.0, max(0.0, disagree_pct + daily_drift * 1.0)), 1)
    f48 = round(min(100.0, max(0.0, disagree_pct + daily_drift * 1.8)), 1)
    f72 = round(min(100.0, max(0.0, disagree_pct + daily_drift * 2.4)), 1)

    emerging_controversy_count = sum(1 for t in themes if t.get('emerging') and t.get('stance', {}).get('Disagree', 0) > t.get('stance', {}).get('Agree', 0))
    risk_score = min(100, max(5, int(disagree_pct * 0.8 + max(0.0, velocity) * 1.5 + emerging_controversy_count * 15)))
    risk_level = 'Critical' if risk_score >= 70 else 'Elevated' if risk_score >= 45 else 'Moderate' if risk_score >= 25 else 'Low'

    strategic_actions = []
    if risk_score >= 45:
        top_theme_title = themes[0]['title'] if themes else 'General friction points'
        strategic_actions.append(f"Deploy targeted strategic communication addressing core controversy theme: “{top_theme_title}”.")
        strategic_actions.append("Activate high-frequency monitoring: negative drift velocity indicates potential escalation.")
    else:
        strategic_actions.append(f"Public sentiment is steady. Disagreement is contained at {disagree_pct}% with low PR escalation risk.")
        strategic_actions.append("Amplify positive feedback themes in forthcoming communications.")

    forecast = {
        'velocity_pp_per_day': round(velocity, 2),
        'crisis_risk_score': risk_score,
        'crisis_risk_level': risk_level,
        'disagree_current_pct': disagree_pct,
        'agree_current_pct': agree_pct,
        'projections': [
            {'horizon': '+24 Hours', 'projected_disagreement': f24, 'trend': 'Increasing' if daily_drift > 1 else 'Decreasing' if daily_drift < -1 else 'Stable'},
            {'horizon': '+48 Hours', 'projected_disagreement': f48, 'trend': 'Increasing' if daily_drift > 1 else 'Decreasing' if daily_drift < -1 else 'Stable'},
            {'horizon': '+72 Hours', 'projected_disagreement': f72, 'trend': 'Increasing' if daily_drift > 1 else 'Decreasing' if daily_drift < -1 else 'Stable'}
        ],
        'strategic_actions': strategic_actions
    }

    return {'count':len(posts),'sentiment':dict(sentiment),'stance':counts(posts),'reviewed':sum(bool(p['review_label']) for p in posts),'timeline':[{'date':key,**val} for key,val in sorted(timeline.items())],'recent_count':len(current),'previous_count':len(prior),'negative_shift_pp':shift,'themes':themes,'insights':insights,'languages':dict(Counter(p['language'] for p in posts)),'recent_stance':counts(current),'previous_stance':counts(prior),'forecast':forecast}
