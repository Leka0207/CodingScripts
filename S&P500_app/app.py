"""
S&P 500 Stock Price Prediction — Interactive Dashboard
=======================================================
Launch:  streamlit run app.py
Data:    Place 'all_stocks_5yr.csv' in the same directory, or upload via sidebar.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso, LogisticRegression
from sklearn.ensemble import (RandomForestRegressor, GradientBoostingRegressor,
                              RandomForestClassifier, GradientBoostingClassifier)
from sklearn.metrics import (mean_squared_error, mean_absolute_error, r2_score,
                             accuracy_score, precision_score, recall_score,
                             f1_score, roc_curve, auc, confusion_matrix)
import warnings, os
warnings.filterwarnings("ignore")

# ─── Page Config ────────────────────────────────────────────────
st.set_page_config(page_title="S&P 500 Predictor", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .block-container { padding-top: 1rem; max-width: 1400px; }
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    .metric-card {
        background: linear-gradient(135deg, #1E2761 0%, #2E86AB 100%);
        padding: 1.2rem; border-radius: 14px; color: white;
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h3 { margin: 0; font-size: 0.8rem; opacity: 0.85; font-weight: 400; }
    .metric-card h1 { margin: 0.2rem 0 0 0; font-size: 1.7rem; font-weight: 700; }
    .insight-box {
        background: #F0F7FF; border-left: 4px solid #2E86AB;
        padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin: 0.8rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sector Map ─────────────────────────────────────────────────
SECTOR_MAP = {
    "Technology": ["AAPL","MSFT","GOOGL","GOOG","FB","INTC","CSCO","ORCL","IBM","ADBE",
                   "CRM","AVGO","TXN","QCOM","NVDA","MU","AMAT","LRCX","XLNX","SWKS"],
    "Finance": ["JPM","BAC","WFC","GS","MS","C","AXP","USB","BK","PNC","COF","CME",
                "SCHW","BLK","AIG","MET","PRU","AFL","ALL","TRV"],
    "Healthcare": ["JNJ","PFE","UNH","MRK","ABBV","ABT","MDT","AMGN","BMY","LLY",
                   "GILD","CELG","BIIB","ISRG","SYK","BDX","ZBH","BAX","EW","VRTX"],
    "Consumer": ["AMZN","WMT","KO","PEP","PG","NKE","MCD","SBUX","HD","LOW",
                 "TGT","COST","CL","KMB","GIS","K","HSY","MKC","SJM","CPB"],
    "Energy": ["XOM","CVX","COP","SLB","EOG","PSX","VLO","MPC","OXY","HAL",
               "APC","DVN","NBL","RRC","CHK","MRO","HES","APA","NOV","HP"],
    "Industrial": ["BA","GE","MMM","CAT","HON","UPS","LMT","UNP","DE","FDX",
                   "RTN","EMR","ETN","ROK","PH","IR","GD","NOC","TXT","ITW"],
}

FEATURES = [
    "open", "high", "low", "close", "volume",
    "price_range", "price_range_pct", "open_close_diff", "pct_change_price",
    "prev_volume", "pct_change_vol",
    "close_vs_ma5", "close_vs_ma20", "vol_vs_ma5", "prev_day_return",
]
TARGET = "pct_change_next_day"


# ─── Data Loading ───────────────────────────────────────────────
@st.cache_data(show_spinner="Loading and processing data...")
def load_and_process(file):
    df = pd.read_csv(file)
    # ── FIX: normalise column names to lowercase & strip whitespace ──
    df.columns = df.columns.str.strip().str.lower()
    # ── Also normalise the stock-ticker column (could be "Name" or "name") ──
    if "name" in df.columns and "Name" not in df.columns:
        df.rename(columns={"name": "Name"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["open","high","low","close"]).sort_values(["Name","date"]).reset_index(drop=True)
    df["next_day_close"] = df.groupby("Name")["close"].shift(-1)
    df["pct_change_next_day"] = ((df["next_day_close"]-df["close"])/df["close"])*100
    df["price_range"] = df["high"]-df["low"]
    df["price_range_pct"] = (df["price_range"]/df["open"])*100
    df["open_close_diff"] = df["close"]-df["open"]
    df["pct_change_price"] = ((df["close"]-df["open"])/df["open"])*100
    df["prev_volume"] = df.groupby("Name")["volume"].shift(1)
    df["pct_change_vol"] = ((df["volume"]-df["prev_volume"])/df["prev_volume"])*100
    df["close_ma5"] = df.groupby("Name")["close"].transform(lambda x: x.rolling(5).mean())
    df["close_ma20"] = df.groupby("Name")["close"].transform(lambda x: x.rolling(20).mean())
    df["vol_ma5"] = df.groupby("Name")["volume"].transform(lambda x: x.rolling(5).mean())
    df["close_vs_ma5"] = ((df["close"]-df["close_ma5"])/df["close_ma5"])*100
    df["close_vs_ma20"] = ((df["close"]-df["close_ma20"])/df["close_ma20"])*100
    df["vol_vs_ma5"] = ((df["volume"]-df["vol_ma5"])/df["vol_ma5"])*100
    df["prev_day_return"] = df.groupby("Name")["pct_change_price"].shift(1)
    s2s = {t: s for s, ts in SECTOR_MAP.items() for t in ts}
    df["sector"] = df["Name"].map(s2s).fillna("Other")
    return df


@st.cache_data(show_spinner="Training models...")
def train_models(_df_clean, split_date_str):
    split_ts = pd.Timestamp(split_date_str)
    train = _df_clean[_df_clean.date < split_ts]
    test = _df_clean[_df_clean.date >= split_ts]
    sc = StandardScaler()
    X_tr = sc.fit_transform(train[FEATURES]); X_te = sc.transform(test[FEATURES])
    y_tr = train[TARGET]; y_te = test[TARGET]
    y_te_cls = (y_te > 0).astype(int)

    n_s = min(80000, len(train))
    idx = np.random.RandomState(42).choice(len(train), n_s, replace=False)
    X_s = X_tr[idx]; y_s = y_tr.iloc[idx]; y_s_cls = (y_s > 0).astype(int)

    reg_m = {"Linear Regression": LinearRegression(), "Ridge": Ridge(alpha=1.0),
             "Lasso": Lasso(alpha=0.01),
             "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=8, min_samples_leaf=30, random_state=42, n_jobs=-1),
             "Gradient Boosting": GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42, subsample=0.8)}
    rr = {}; rp = {}; rt = {}
    for nm, m in reg_m.items():
        xtr = X_tr if nm in ["Linear Regression","Ridge","Lasso"] else X_s
        ytr = y_tr if nm in ["Linear Regression","Ridge","Lasso"] else y_s
        m.fit(xtr, ytr); yp = m.predict(X_te); rp[nm] = yp; rt[nm] = m
        da = ((y_te.values > 0) == (yp > 0)).mean() * 100
        rr[nm] = {"RMSE": round(np.sqrt(mean_squared_error(y_te,yp)),4), "MAE": round(mean_absolute_error(y_te,yp),4),
                  "R²": round(r2_score(y_te,yp),4), "Dir Accuracy (%)": round(da,2)}

    cls_m = {"Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
             "RF Classifier": RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=30, random_state=42, n_jobs=-1),
             "GB Classifier": GradientBoostingClassifier(n_estimators=50, max_depth=3, learning_rate=0.05, random_state=42, subsample=0.8)}
    cr = {}; cp = {}
    for nm, m in cls_m.items():
        m.fit(X_s, y_s_cls); yp = m.predict(X_te); yprob = m.predict_proba(X_te)[:,1]; cp[nm] = yprob
        fpr, tpr, _ = roc_curve(y_te_cls, yprob)
        cr[nm] = {"Accuracy": round(accuracy_score(y_te_cls,yp),4), "Precision": round(precision_score(y_te_cls,yp),4),
                  "Recall": round(recall_score(y_te_cls,yp),4), "F1-Score": round(f1_score(y_te_cls,yp),4),
                  "AUC": round(auc(fpr,tpr),4)}

    return (pd.DataFrame(rr).T, rp, rt, pd.DataFrame(cr).T, cp, test, y_te, y_te_cls, sc)


# ─── Sidebar ────────────────────────────────────────────────────
st.sidebar.markdown("## 📈 S&P 500 Predictor")
st.sidebar.markdown("---")
uploaded = st.sidebar.file_uploader("Upload `all_stocks_5yr.csv`", type=["csv","data"])
use_sample = st.sidebar.checkbox("Use local file path", value=True)

data_path = None
if uploaded: data_path = uploaded
elif use_sample:
    for p in ["all_stocks_5yr.csv", "sp500_data/all_stocks_5yr.csv"]:
        if os.path.exists(p): data_path = p; break

if not data_path:
    st.info("👈 Upload the S&P 500 CSV or check 'Use local file path'.")
    st.stop()

df = load_and_process(data_path)
dc = df.dropna(subset=FEATURES+[TARGET]).copy()
dc = dc[~dc[FEATURES+[TARGET]].isin([np.inf,-np.inf]).any(axis=1)].reset_index(drop=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### Settings")
split_date = st.sidebar.date_input("Train/Test Split", value=pd.Timestamp("2017-02-08"),
                                    min_value=dc.date.min().date(), max_value=dc.date.max().date())
all_stocks = sorted(dc.Name.unique())
sectors_list = ["All"] + sorted(SECTOR_MAP.keys()) + ["Other"]
sel_sector = st.sidebar.selectbox("Sector Filter", sectors_list)
avail = dc[dc.sector==sel_sector].Name.unique().tolist() if sel_sector!="All" else all_stocks
defaults = [s for s in ["AAPL","MSFT","GOOGL","AMZN","JPM","BA"] if s in avail][:6]
sel_stocks = st.sidebar.multiselect("Spotlight Stocks", avail, default=defaults)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(dc):,}** records · **{dc.Name.nunique()}** stocks")

# Train
reg_df, reg_preds, reg_trained, cls_df, cls_probs, test_df, y_test, y_test_cls, scaler = train_models(dc, str(split_date))
best_reg = reg_df["R²"].idxmax(); best_preds = reg_preds[best_reg]

# ─── Header ─────────────────────────────────────────────────────
st.title("S&P 500 Stock Price Prediction Dashboard")
st.caption("Next-day price prediction using supervised learning on 5 years of daily data")
c1,c2,c3,c4,c5 = st.columns(5)
for col, label, val in zip([c1,c2,c3,c4,c5],
    ["Records","Stocks","Best R²","Best Dir Acc","Best F1"],
    [f"{len(dc):,}", str(dc.Name.nunique()), f"{reg_df['R²'].max():.4f}",
     f"{reg_df['Dir Accuracy (%)'].max():.1f}%", f"{cls_df['F1-Score'].max():.3f}"]):
    with col:
        st.markdown(f'<div class="metric-card"><h3>{label}</h3><h1>{val}</h1></div>', unsafe_allow_html=True)
st.markdown("")

# ─── Tabs ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📊 Explorer", "🤖 Regression", "🎯 Classification", "🏢 Sectors", "🔬 Feature Lab", "🔮 Predict"])

# ── TAB 1: EXPLORER ──
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        sub = dc[dc.Name.isin(sel_stocks)] if sel_stocks else dc.head(1000)
        fig = px.line(sub, x="date", y="close", color="Name", title="Daily Closing Prices",
                      labels={"close":"Close ($)","date":""})
        fig.update_layout(height=420, template="plotly_white", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.histogram(dc, x=TARGET, nbins=120, title="Next-Day % Change Distribution",
                           color_discrete_sequence=["#2E86AB"], marginal="box")
        fig.update_layout(height=420, template="plotly_white"); fig.update_xaxes(range=[-6,6])
        st.plotly_chart(fig, use_container_width=True)

    # Deep dive
    st.markdown("### 🔍 Stock Deep Dive")
    dive_s = st.selectbox("Select stock:", all_stocks, index=all_stocks.index("AAPL") if "AAPL" in all_stocks else 0)
    dive = dc[dc.Name==dive_s]
    m1,m2,m3 = st.columns(3)
    m1.metric("Avg Return", f"{dive[TARGET].mean():.3f}%")
    m2.metric("Volatility", f"{dive[TARGET].std():.3f}%")
    m3.metric("Trading Days", f"{len(dive):,}")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65,0.35], vertical_spacing=0.08,
                        subplot_titles=["Price + 20-day MA", "Volume"])
    fig.add_trace(go.Scatter(x=dive.date, y=dive.close, line=dict(color="#1E2761",width=1.5), name="Close"), row=1, col=1)
    fig.add_trace(go.Scatter(x=dive.date, y=dive.close_ma20, line=dict(color="#E74C3C",width=1,dash="dash"), name="20d MA"), row=1, col=1)
    fig.add_trace(go.Bar(x=dive.date, y=dive.volume, marker_color="#2E86AB", opacity=0.5, name="Volume"), row=2, col=1)
    fig.update_layout(height=500, template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# ── TAB 2: REGRESSION ──
with tab2:
    st.subheader("Regression Model Results")
    st.dataframe(reg_df.style.highlight_max(axis=0, subset=["R²","Dir Accuracy (%)"], color="#d4edda")
                 .highlight_min(axis=0, subset=["RMSE","MAE"], color="#d4edda"), use_container_width=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        for m in ["RMSE","MAE"]:
            fig.add_trace(go.Bar(name=m, x=reg_df.index, y=reg_df[m], text=reg_df[m].round(4), textposition="outside"))
        fig.update_layout(title="Error Metrics", barmode="group", height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        colors = ["#3498db","#2ecc71","#e74c3c","#f39c12","#9b59b6"]
        fig = go.Figure(go.Bar(x=reg_df.index, y=reg_df["Dir Accuracy (%)"], marker_color=colors,
                               text=reg_df["Dir Accuracy (%)"].round(1), textposition="outside"))
        fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50% baseline")
        fig.update_layout(title="Direction Accuracy", height=400, template="plotly_white", yaxis_range=[48,55])
        st.plotly_chart(fig, use_container_width=True)

    sel_m = st.selectbox("Inspect model:", list(reg_preds.keys()), index=list(reg_preds.keys()).index(best_reg))
    ps = reg_preds[sel_m]; n = min(3000, len(y_test))
    c1,c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=y_test.values[:n], y=ps[:n], mode="markers",
                                 marker=dict(size=3,opacity=0.3,color="#3498db"), name="Pred"))
        fig.add_trace(go.Scatter(x=[-6,6], y=[-6,6], mode="lines", line=dict(dash="dash",color="red"), name="Perfect"))
        fig.update_layout(title="Actual vs Predicted", height=420, template="plotly_white",
                          xaxis_range=[-6,6], yaxis_range=[-6,6])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.histogram((y_test.values-ps).clip(-6,6), nbins=80, title="Residuals",
                           color_discrete_sequence=["#9b59b6"])
        fig.add_vline(x=0, line_dash="dash", line_color="red")
        fig.update_layout(height=420, template="plotly_white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Feature Importance")
    c1,c2 = st.columns(2)
    for col, mn in zip([c1,c2], ["Random Forest","Gradient Boosting"]):
        with col:
            imp = pd.Series(reg_trained[mn].feature_importances_, index=FEATURES).sort_values()
            fig = px.bar(imp, orientation="h", title=mn, color=imp.values, color_continuous_scale="Greens")
            fig.update_layout(height=400, template="plotly_white", showlegend=False, coloraxis_showscale=False, yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 3: CLASSIFICATION ──
with tab3:
    st.subheader("Direction Prediction (Up/Down)")
    st.dataframe(cls_df.style.highlight_max(axis=0, color="#d4edda"), use_container_width=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        for m in ["Accuracy","Precision","Recall","F1-Score"]:
            fig.add_trace(go.Bar(name=m, x=cls_df.index, y=cls_df[m], text=cls_df[m].round(4), textposition="outside"))
        fig.update_layout(title="Classification Metrics", barmode="group", height=420, template="plotly_white", yaxis_range=[0.4,1.0])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure()
        cc = ["#3498db","#e74c3c","#2ecc71"]
        for (nm,pr),c in zip(cls_probs.items(), cc):
            fpr,tpr,_ = roc_curve(y_test_cls, pr)
            fig.add_trace(go.Scatter(x=fpr, y=tpr, line=dict(color=c,width=2), name=f"{nm} (AUC={auc(fpr,tpr):.4f})"))
        fig.add_trace(go.Scatter(x=[0,1], y=[0,1], line=dict(dash="dash",color="gray"), name="Random"))
        fig.update_layout(title="ROC Curves", height=420, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Confusion Matrices")
    cols = st.columns(3)
    for col,(nm,pr) in zip(cols, cls_probs.items()):
        with col:
            pc = (pr>0.5).astype(int); cm = confusion_matrix(y_test_cls, pc)
            fig = px.imshow(cm, text_auto=True, color_continuous_scale="Blues", x=["Down","Up"], y=["Down","Up"], title=nm)
            fig.update_layout(height=320, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 4: SECTORS ──
with tab4:
    st.subheader("Sector-Level Performance")
    te = test_df.copy(); te["predicted"] = best_preds
    sr = []
    for sec,tk in SECTOR_MAP.items():
        m = te.Name.isin(tk)
        if m.sum()>0:
            s = te[m]
            sr.append({"Sector":sec, "Stocks":s.Name.nunique(),
                       "MAE":round(mean_absolute_error(s[TARGET],s["predicted"]),4),
                       "Dir Accuracy (%)":round(((s[TARGET]>0)==(s["predicted"]>0)).mean()*100,2)})
    sdf = pd.DataFrame(sr).sort_values("Dir Accuracy (%)", ascending=False)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(sdf, x="Sector", y="Dir Accuracy (%)", color="Dir Accuracy (%)",
                     color_continuous_scale="RdYlGn", text="Dir Accuracy (%)", title="Direction Accuracy")
        fig.add_hline(y=50, line_dash="dash", line_color="red")
        fig.update_layout(height=400, template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(sdf, x="Sector", y="MAE", color="MAE", color_continuous_scale="OrRd",
                     text="MAE", title="Mean Absolute Error")
        fig.update_layout(height=400, template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(sdf.set_index("Sector"), use_container_width=True)

    st.markdown("### Per-Stock Breakdown")
    sf = st.selectbox("Sector:", list(SECTOR_MAP.keys()), key="sec_det")
    tk_in = [t for t in SECTOR_MAP[sf] if t in te.Name.unique()]
    if tk_in:
        sp = te[te.Name.isin(tk_in)].groupby("Name").apply(
            lambda g: pd.Series({"MAE":mean_absolute_error(g[TARGET],g["predicted"]),
                                  "Dir Acc (%)":((g[TARGET]>0)==(g["predicted"]>0)).mean()*100})).round(2)
        sp = sp.sort_values("Dir Acc (%)", ascending=False)
        fig = px.bar(sp.reset_index(), x="Name", y="Dir Acc (%)", color="Dir Acc (%)",
                     color_continuous_scale="RdYlGn", title=f"{sf} — Per-Stock Accuracy")
        fig.add_hline(y=50, line_dash="dash", line_color="red")
        fig.update_layout(height=400, template="plotly_white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Rolling Accuracy")
    te["correct"] = ((te[TARGET]>0)==(te["predicted"]>0)).astype(int)
    ra = te.groupby("date")["correct"].mean().mul(100).rolling(20).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ra.index, y=ra.values, fill="tozeroy", line=dict(color="#2E86AB")))
    fig.add_hline(y=50, line_dash="dash", line_color="red", annotation_text="50%")
    fig.update_layout(title="20-Day Rolling Direction Accuracy", height=350, template="plotly_white", yaxis_range=[35,65])
    st.plotly_chart(fig, use_container_width=True)

# ── TAB 5: FEATURE LAB ──
with tab5:
    st.subheader("Feature Exploration Lab")
    c1,c2 = st.columns(2)
    with c1:
        corr = dc[FEATURES+[TARGET]].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        title="Correlation Matrix", aspect="auto")
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fx = st.selectbox("X-axis:", FEATURES, index=FEATURES.index("pct_change_price"))
        fy = st.selectbox("Y-axis:", [TARGET]+FEATURES, index=0)
        samp = dc.sample(n=min(5000,len(dc)), random_state=42)
        fig = px.scatter(samp, x=fx, y=fy, opacity=0.2, trendline="ols",
                         color_discrete_sequence=["#E74C3C"], title=f"{fx} vs {fy}")
        fig.update_layout(height=550, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Lasso Feature Selection")
    lm = reg_trained.get("Lasso")
    if lm:
        coefs = pd.Series(lm.coef_, index=FEATURES).sort_values()
        fig = px.bar(coefs, orientation="h", title="Lasso Coefficients", color=coefs.abs().values,
                     color_continuous_scale="Oranges")
        fig.update_layout(height=400, template="plotly_white", coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"**Non-zero features:** {(coefs.abs()>0.0001).sum()} / {len(FEATURES)}")

# ── TAB 6: PREDICT ──
with tab6:
    st.subheader("🔮 Live Prediction Tool")
    st.markdown("Enter today's trading data to predict tomorrow's price movement.")
    with st.form("pred"):
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown("**Price**")
            io = st.number_input("Open ($)", value=150.0, step=1.0)
            ih = st.number_input("High ($)", value=153.0, step=1.0)
            il = st.number_input("Low ($)", value=148.0, step=1.0)
            ic = st.number_input("Close ($)", value=151.0, step=1.0)
            iv = st.number_input("Volume", value=50_000_000, step=1_000_000)
        with c2:
            st.markdown("**Context**")
            ipv = st.number_input("Prev Day Volume", value=48_000_000, step=1_000_000)
            im5 = st.number_input("5-Day MA ($)", value=150.0, step=1.0)
            im20 = st.number_input("20-Day MA ($)", value=148.0, step=1.0)
            ivm5 = st.number_input("5-Day Vol MA", value=49_000_000, step=1_000_000)
            ipr = st.number_input("Prev Day Return (%)", value=0.0, step=0.1)
        with c3:
            st.markdown("**Info**")
            st.info("Fill in the fields and click Predict to see all model outputs.")
        sub = st.form_submit_button("🚀 Predict", use_container_width=True)
    if sub:
        pr=ih-il; prp=pr/io*100 if io else 0; ocd=ic-io
        pcp=(ic-io)/io*100 if io else 0; pcv=(iv-ipv)/ipv*100 if ipv else 0
        cv5=(ic-im5)/im5*100 if im5 else 0; cv20=(ic-im20)/im20*100 if im20 else 0
        vv5=(iv-ivm5)/ivm5*100 if ivm5 else 0
        row = np.array([[io,ih,il,ic,iv,pr,prp,ocd,pcp,ipv,pcv,cv5,cv20,vv5,ipr]])
        row_s = scaler.transform(row)
        st.markdown("### All Model Predictions")
        cols = st.columns(len(reg_trained))
        for col,(nm,m) in zip(cols, reg_trained.items()):
            with col:
                v = m.predict(row_s)[0]
                icon = "🟢" if v>0 else "🔴"
                st.metric(nm, f"{icon} {v:+.4f}%", "UP" if v>0 else "DOWN")
        st.markdown('<div class="insight-box"><strong>Disclaimer:</strong> Predictions are based on '
                    'technical features only. Always incorporate fundamental analysis and risk management.</div>',
                    unsafe_allow_html=True)

st.markdown("---")
st.markdown("<div style='text-align:center;color:#999;font-size:0.85rem;'>"
            "S&P 500 Predictor — Streamlit + Scikit-learn + Plotly</div>", unsafe_allow_html=True)
