import streamlit as st
from scanner import scan, US, IDX
st.set_page_config(page_title='Accumulation & Breakout Scanner',layout='wide')
st.title('US + IDX | Accumulation & Breakout Scanner')
st.caption('Research prototype. Delayed/third-party data; no verified market-maker positions or live insider feed.')
market=st.selectbox('Market',['BOTH','US','IDX'])
def_tickers=(US if market in ('BOTH','US') else [])+([x+'.JK' for x in IDX] if market in ('BOTH','IDX') else [])
tickers=st.text_area('Symbols (space or comma separated)',' '.join(def_tickers))
if st.button('Run scan',type='primary'):
    with st.spinner('Fetching price data and computing signals...'):
        result,errors=scan(tickers.replace(',',' ').split())
    if not result.empty:
        st.dataframe(result.sort_values('score_technical',ascending=False),use_container_width=True,hide_index=True)
        st.download_button('Download CSV',result.to_csv(index=False),'signals.csv','text/csv')
    if not errors.empty:st.warning('Some tickers could not be analyzed');st.dataframe(errors)
st.info('Technical score excludes catalysts and insider activity. Signals are research flags, not trade instructions.')
