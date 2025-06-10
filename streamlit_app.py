import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import time

# Parámetros de WACC realista
Rf = 0.0435
Rm = 0.085
Tc = 0.21

def calcular_wacc(info, balance_sheet):
    try:
        beta = info.get("beta")
        price = info.get("currentPrice")
        shares = info.get("sharesOutstanding")
        market_cap = price * shares if price and shares else None

        lt_debt = balance_sheet.loc["Long Term Debt", :].iloc[0] if "Long Term Debt" in balance_sheet.index else 0
        st_debt = balance_sheet.loc["Short Long Term Debt", :].iloc[0] if "Short Long Term Debt" in balance_sheet.index else 0
        total_debt = lt_debt + st_debt

        Re = Rf + beta * (Rm - Rf) if beta is not None else None
        Rd = 0.055 if total_debt > 0 else 0

        E = market_cap
        D = total_debt

        if not Re or not E or not D or E + D == 0:
            return None, total_debt

        wacc = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - Tc)
        return wacc, total_debt
    except:
        return None, None

def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        price = info.get("currentPrice")
        name = info.get("longName")
        sector = info.get("sector")
        country = info.get("country")
        industry = info.get("industry")
        pe = info.get("trailingPE")
        pb = info.get("priceToBook")
        dividend = info.get("dividendRate")
        dividend_yield = info.get("dividendYield")
        payout = info.get("payoutRatio")
        roa = info.get("returnOnAssets")
        roe = info.get("returnOnEquity")
        current_ratio = info.get("currentRatio")
        ltde = info.get("longTermDebtEquity")
        de = info.get("debtToEquity")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("netMargins")

        fcf = cf.loc["Total Cash From Operating Activities", :].iloc[0] if "Total Cash From Operating Activities" in cf.index else None
        shares = info.get("sharesOutstanding")
        pfcf = price / (fcf / shares) if fcf and shares else None

        ebit = fin.loc["EBIT", :].iloc[0] if "EBIT" in fin.index else None
        equity = bs.loc["Total Stockholder Equity", :].iloc[0] if "Total Stockholder Equity" in bs.index else None

        wacc, total_debt = calcular_wacc(info, bs)

        capital_invertido = total_debt + equity if total_debt and equity else None
        roic = ebit / capital_invertido if ebit and capital_invertido else None
        eva = roic - wacc if roic and wacc else None

        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "EVA": eva,
            "Deuda Total": total_debt,
            "Patrimonio Neto": equity,
        }

    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Interfaz de usuario
st.set_page_config(page_title="Dashboard Financiero", layout="wide")
st.title("📊 Dashboard de Análisis Financiero - WACC, ROIC, EVA y Solvencia")

tickers_input = st.text_area("🔎 Ingresa hasta 50 tickers separados por coma", "AAPL,MSFT,GOOGL,TSLA,AMZN")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if len(tickers) > 50:
    st.warning("⚠️ Máximo permitido: 50 tickers. Se tomarán solo los primeros 50.")
    tickers = tickers[:50]

if st.button("🔍 Analizar"):
    resultados = []
    for i, t in enumerate(tickers):
        st.write(f"⏳ Procesando {t} ({i+1}/{len(tickers)})...")
        resultados.append(get_data(t))
        time.sleep(1.5)

    df = pd.DataFrame(resultados).drop(columns=["Deuda Total", "Patrimonio Neto", "Error"], errors="ignore")
    st.subheader("📋 Ratios Financieros")
    st.dataframe(df, use_container_width=True)

    selected = st.selectbox("📌 Selecciona una empresa para ver su deuda vs. capital:", df["Ticker"])
    detalle = next((d for d in resultados if d["Ticker"] == selected), None)
    if detalle:
        st.subheader("💳 Análisis de Solvencia de Deuda")
        deuda_df = pd.DataFrame({
            "Categoría": ["Deuda Total", "Patrimonio Neto"],
            "Valor (USD)": [detalle["Deuda Total"], detalle["Patrimonio Neto"]]
        })
        st.dataframe(deuda_df)

        fig, ax = plt.subplots()
        ax.barh(deuda_df["Categoría"], deuda_df["Valor (USD)"])
        ax.set_xlabel("USD")
        ax.set_title(f"Deuda vs Capital - {selected}")
        st.pyplot(fig)
