from typing import Any, Dict, Optional, List
import re
from datetime import datetime, timedelta, timezone

import yfinance as yf
from curl_cffi import requests as curl_requests

from langchain_core.messages import HumanMessage, SystemMessage

from core.llm import get_solar_chat


_TICKER_TOKEN_RE = re.compile(r"[A-Za-z0-9.\-]+")


def resolve_ticker(stock_name: str) -> str:
    """
    종목명을 티커로 변환합니다.
    - 이미 티커처럼 보이면 그대로 사용
    - 숫자 6자리면 KRX 기본(.KS)으로 가정
    - 그렇지 않으면 LLM으로 티커 추정
    """
    raw = (stock_name or "").strip()
    if not raw:
        return raw

    if re.fullmatch(r"\d{6}", raw):
        return f"{raw}.KS"

    if re.fullmatch(r"[A-Za-z0-9.\-]+", raw):
        return raw.upper()

    try:
        llm = get_solar_chat()
        messages = [
            SystemMessage(
                content=(
                    "You convert company names to tickers. "
                    "Return a single ticker token only (e.g., AAPL, TSLA, 005930.KS)."
                )
            ),
            HumanMessage(content=f"Company name: {raw}"),
        ]
        response = llm.invoke(messages)
        text = response.content if isinstance(response.content, str) else str(response.content)
        match = _TICKER_TOKEN_RE.search(text)
        return match.group(0).upper() if match else raw
    except Exception:
        return raw


def generate_llm_chart_analysis(payload: Dict[str, Any]) -> Optional[str]:
    """
    기술적 분석 결과를 LLM에 전달해 요약/해석을 생성합니다.
    """
    try:
        llm = get_solar_chat()
        messages = [
            SystemMessage(
                content=(
                    "You are a technical analysis summarizer. "
                    "Summarize chart/indicator context factually without investment advice."
                )
            ),
            HumanMessage(
                content=(
                    "Given the structured technical data, write a brief analysis in Korean. "
                    "No buy/sell recommendations.\n"
                    f"{payload}"
                )
            ),
        ]
        response = llm.invoke(messages)
        text = response.content if isinstance(response.content, str) else str(response.content)
        return text.strip()
    except Exception:
        return None


def node6_stock_analyst(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Node6: 주식 기술적 분석
    - 종목명, 매수/매도 날짜를 받아서 실제 주가 데이터를 가져옴
    - 기술적 지표(볼린저밴드, RSI, MACD 등)를 계산
    - 구조화된 분석 결과를 반환
    - LLM을 통해 차트 해석 요약을 추가
    """
    stock_name = state.get("layer1_stock")
    buy_date = state.get("layer2_buy_date")
    sell_date = state.get("layer2_sell_date")
    decision_basis = state.get("layer3_decision_basis")

    # 입력 검증
    if not stock_name or not buy_date or not sell_date:
        return {"n6_stock_analysis": fallback_result("필수 입력값이 누락되었습니다.")}

    try:
        ticker = resolve_ticker(stock_name)
        # 주가 데이터 가져오기
        stock_data = fetch_stock_data(ticker, buy_date, sell_date)
        if not stock_data:
            return {"n6_stock_analysis": fallback_result("주가 데이터를 가져올 수 없습니다.")}

        # 기술적 분석 수행
        analysis_result = perform_technical_analysis(stock_data, buy_date, sell_date)
        analysis_result["stock_analysis"]["ticker"] = ticker
        analysis_result["stock_analysis"]["resolved_from"] = stock_name

        llm_analysis = generate_llm_chart_analysis(
            {
                "ticker": ticker,
                "period": analysis_result["stock_analysis"].get("period"),
                "summary": analysis_result["stock_analysis"].get("summary"),
                "price_move": analysis_result["stock_analysis"].get("price_move"),
                "trend": analysis_result["stock_analysis"].get("trend"),
                "indicators": analysis_result["stock_analysis"].get("indicators"),
                "volume_analysis": analysis_result["stock_analysis"].get("volume_analysis"),
                "risk_notes": analysis_result["stock_analysis"].get("risk_notes"),
            }
        )
        if llm_analysis:
            analysis_result["stock_analysis"]["llm_chart_analysis"] = llm_analysis

        # 결과 검증
        from utils.validator import validate_node6

        if not validate_node6(analysis_result):
            return {"n6_stock_analysis": fallback_result("분석 결과 검증에 실패했습니다.")}

        return {"n6_stock_analysis": analysis_result}

    except Exception as e:
        return {"n6_stock_analysis": fallback_result(f"분석 중 오류 발생: {str(e)}")}



def fetch_stock_data(stock_name: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    Yahoo chart API를 curl_cffi로 호출하고, 실패 시 yfinance로 fallback
    볼린저밴드 계산을 위해 매수/매도일 기준 ±1개월 데이터를 수집합니다.

    Args:
        stock_name: 종목명 또는 티커 (예: AAPL, TSLA, 005930.KS)
        start_date: 시작일 (YYYY-MM-DD) - 매수일
        end_date: 종료일 (YYYY-MM-DD) - 매도일

    Returns:
        주가 데이터 딕셔너리 또는 None
    """
    try:
        # 볼린저밴드 계산을 위해 기간 확장 (±1개월)
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        extended_start = (start_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        extended_end = (end_dt + timedelta(days=30)).strftime("%Y-%m-%d")

        chart = _fetch_yahoo_chart(stock_name, extended_start, extended_end)
        if chart:
            chart["start_date"] = start_date
            chart["end_date"] = end_date
            chart["extended_start"] = extended_start
            chart["extended_end"] = extended_end
            return chart

        ticker = yf.Ticker(stock_name)
        hist = ticker.history(start=extended_start, end=extended_end)

        if hist.empty:
            return None

        return {
            "ticker": stock_name,
            "start_date": start_date,  # 원래 매수일 유지
            "end_date": end_date,  # 원래 매도일 유지
            "extended_start": extended_start,  # 확장된 시작일
            "extended_end": extended_end,  # 확장된 종료일
            "open": hist["Open"].tolist(),
            "high": hist["High"].tolist(),
            "low": hist["Low"].tolist(),
            "close": hist["Close"].tolist(),
            "volume": hist["Volume"].tolist(),
            "dates": hist.index.strftime("%Y-%m-%d").tolist(),
        }
    except Exception as e:
        print(f"주가 데이터 가져오기 실패: {e}")
        return None


def _fetch_yahoo_chart(stock_name: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    start_ts = _to_unix_date(start_date)
    end_ts = _to_unix_date(end_date)
    if start_ts is None or end_ts is None:
        return None

    end_ts += 24 * 60 * 60
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock_name}"
    params = {
        "period1": str(start_ts),
        "period2": str(end_ts),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }

    try:
        response = curl_requests.get(url, params=params, impersonate="chrome120", timeout=20)
        if response.status_code != 200:
            print(f"Yahoo chart API error: {response.status_code}")
            return None

        payload = response.json()
        result = payload.get("chart", {}).get("result")
        if not result:
            return None

        data = result[0]
        timestamps = data.get("timestamp") or []
        indicators = data.get("indicators", {}).get("quote", [])
        if not timestamps or not indicators:
            return None

        quote = indicators[0]
        opens = quote.get("open") or []
        highs = quote.get("high") or []
        lows = quote.get("low") or []
        closes = quote.get("close") or []
        volumes = quote.get("volume") or []

        if not closes:
            return None

        dates = [
            datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            for ts in timestamps
        ]

        return {
            "ticker": stock_name,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
            "dates": dates,
        }
    except Exception as exc:
        print(f"Yahoo chart fetch failed: {exc}")
        return None


def _to_unix_date(date_str: str) -> Optional[int]:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return None


def perform_technical_analysis(stock_data: Dict[str, Any], buy_date: str, sell_date: str) -> Dict[str, Any]:
    """
    기술적 분석을 수행하는 함수

    Args:
        stock_data: fetch_stock_data에서 가져온 주가 데이터
        buy_date: 매수일
        sell_date: 매도일

    Returns:
        구조화된 기술적 분석 결과
    """
    close_prices = stock_data.get("close", [])
    high_prices = stock_data.get("high", [])
    low_prices = stock_data.get("low", [])
    volumes = stock_data.get("volume", [])
    dates = stock_data.get("dates", [])

    # 데이터가 없으면 기본값 반환
    if not close_prices:
        return {
            "stock_analysis": {
                "ticker": stock_data.get("ticker", "unknown"),
                "period": {"buy_date": buy_date, "sell_date": sell_date},
                "summary": "주가 데이터가 충분하지 않습니다.",
                "price_move": {
                    "start_price": "unknown",
                    "end_price": "unknown",
                    "pct_change": "unknown",
                    "highest": "unknown",
                    "lowest": "unknown"
                },
                "trend": "sideways",
                "indicators": [],
                "volume_analysis": {
                    "average_volume": "unknown",
                    "trend": "unknown",
                    "anomalies": []
                },
                "risk_notes": ["데이터 부족"],
                "uncertainty_level": "high"
            }
        }

    # 실제 매수/매도일의 인덱스 찾기
    try:
        buy_idx = dates.index(buy_date)
        sell_idx = dates.index(sell_date)
    except ValueError:
        # 정확한 날짜가 없으면 가장 가까운 날짜 찾기
        buy_idx = 0
        sell_idx = len(close_prices) - 1
        for i, date in enumerate(dates):
            if date >= buy_date:
                buy_idx = i
                break
        for i in range(len(dates) - 1, -1, -1):
            if dates[i] <= sell_date:
                sell_idx = i
                break

    # 가격 분석 (실제 매수/매도일 기준)
    start_price = close_prices[buy_idx]
    end_price = close_prices[sell_idx]
    pct_change = ((end_price - start_price) / start_price) * 100

    # 매수/매도 기간의 최고/최저가
    period_high_prices = high_prices[buy_idx:sell_idx+1]
    period_low_prices = low_prices[buy_idx:sell_idx+1]
    highest = max(period_high_prices) if period_high_prices else max(high_prices)
    lowest = min(period_low_prices) if period_low_prices else min(low_prices)

    # 추세 판단 (간단한 로직)
    if pct_change > 5:
        trend = "up"
    elif pct_change < -5:
        trend = "down"
    else:
        trend = "sideways"

    # 볼린저 밴드 계산
    bb_result = calculate_bollinger_bands(close_prices)

    # RSI 계산
    rsi_values = calculate_rsi(close_prices)
    current_rsi = rsi_values[-1] if rsi_values else None

    # MACD 계산
    macd_result = calculate_macd(close_prices)

    # 지표 해석
    indicators = []

    # 볼린저 밴드 해석
    if bb_result and bb_result.get('upper') and bb_result.get('lower'):
        last_price = close_prices[-1]
        upper_band = bb_result['upper'][-1]
        lower_band = bb_result['lower'][-1]

        if last_price > upper_band:
            bb_interp = "상단 밴드 돌파 - 과매수 구간"
        elif last_price < lower_band:
            bb_interp = "하단 밴드 이탈 - 과매도 구간"
        else:
            bb_interp = "밴드 내 정상 범위"

        indicators.append({
            "name": "bollinger_band",
            "value": f"Upper: {upper_band:.2f}, Lower: {lower_band:.2f}",
            "interpretation": bb_interp
        })

    # RSI 해석
    if current_rsi:
        if current_rsi > 70:
            rsi_interp = "과매수 구간"
        elif current_rsi < 30:
            rsi_interp = "과매도 구간"
        else:
            rsi_interp = "중립 구간"

        indicators.append({
            "name": "rsi",
            "value": f"{current_rsi:.2f}",
            "interpretation": rsi_interp
        })

    # MACD 해석
    if macd_result and macd_result.get('macd') and macd_result.get('signal'):
        macd_line = macd_result['macd']
        signal_line = macd_result['signal']

        current_macd = macd_line[-1]
        current_signal = signal_line[-1]

        if current_macd > current_signal:
            macd_interp = "골든크로스 - 상승 신호"
        else:
            macd_interp = "데드크로스 - 하락 신호"

        indicators.append({
            "name": "macd",
            "value": f"MACD: {current_macd:.2f}, Signal: {current_signal:.2f}",
            "interpretation": macd_interp
        })

    # 거래량 분석
    avg_volume = sum(volumes) / len(volumes) if volumes else 0

    # 리스크 노트 생성
    risk_notes = []
    if abs(pct_change) > 20:
        risk_notes.append("높은 변동성 구간")
    if current_rsi and current_rsi > 70:
        risk_notes.append("과매수 구간 - 조정 가능성")
    if current_rsi and current_rsi < 30:
        risk_notes.append("과매도 구간 - 반등 가능성")

    # 불확실성 레벨 판단
    if len(close_prices) < 20:
        uncertainty = "high"
    elif abs(pct_change) > 15:
        uncertainty = "medium"
    else:
        uncertainty = "low"

    result = {
        "stock_analysis": {
            "ticker": stock_data.get("ticker", "unknown"),
            "period": {
                "buy_date": buy_date,
                "sell_date": sell_date
            },
            "summary": f"{stock_data.get('ticker')} 종목의 기술적 분석 결과입니다. 기간 동안 {pct_change:.2f}%의 수익률을 기록했습니다.",
            "price_move": {
                "start_price": f"{start_price:.2f}",
                "end_price": f"{end_price:.2f}",
                "pct_change": f"{pct_change:.2f}%",
                "highest": f"{highest:.2f}",
                "lowest": f"{lowest:.2f}"
            },
            "trend": trend,
            "indicators": indicators if indicators else [
                {
                    "name": "bollinger_band",
                    "value": "unknown",
                    "interpretation": "데이터 부족으로 계산 불가"
                }
            ],
            "volume_analysis": {
                "average_volume": f"{avg_volume:.0f}",
                "trend": "증가" if volumes and volumes[-1] > avg_volume else "감소",
                "anomalies": []
            },
            "risk_notes": risk_notes if risk_notes else ["정상 범위"],
            "uncertainty_level": uncertainty
        }
    }

    return result


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Optional[Dict[str, List[float]]]:
    """
    볼린저 밴드 계산

    Args:
        prices: 종가 리스트
        period: 이동평균 기간 (기본 20일)
        std_dev: 표준편차 배수 (기본 2)

    Returns:
        {'upper': 상단밴드, 'middle': 중간밴드(SMA), 'lower': 하단밴드}
    """
    if len(prices) < period:
        return None

    upper_band = []
    middle_band = []
    lower_band = []

    for i in range(len(prices)):
        if i < period - 1:
            upper_band.append(None)
            middle_band.append(None)
            lower_band.append(None)
        else:
            # 이동평균 계산
            window = prices[i - period + 1:i + 1]
            sma = sum(window) / period

            # 표준편차 계산
            variance = sum((x - sma) ** 2 for x in window) / period
            std = variance ** 0.5

            middle_band.append(sma)
            upper_band.append(sma + (std * std_dev))
            lower_band.append(sma - (std * std_dev))

    # None이 아닌 값만 반환
    valid_upper = [x for x in upper_band if x is not None]
    valid_middle = [x for x in middle_band if x is not None]
    valid_lower = [x for x in lower_band if x is not None]

    if not valid_upper:
        return None

    return {
        'upper': valid_upper,
        'middle': valid_middle,
        'lower': valid_lower
    }


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[List[float]]:
    """
    RSI (Relative Strength Index) 계산

    Args:
        prices: 종가 리스트
        period: RSI 계산 기간 (기본 14일)

    Returns:
        RSI 값 리스트 (0~100)
    """
    if len(prices) < period + 1:
        return None

    rsi_values = []
    gains = []
    losses = []

    # 가격 변화 계산
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    # 첫 RSI 계산 (단순 평균)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        rsi = 100
    else:
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

    rsi_values.append(rsi)

    # 이후 RSI 계산 (평활 이동평균)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_values.append(rsi)

    return rsi_values


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, List[float]]]:
    """
    MACD (Moving Average Convergence Divergence) 계산

    Args:
        prices: 종가 리스트
        fast: 빠른 EMA 기간 (기본 12일)
        slow: 느린 EMA 기간 (기본 26일)
        signal: 시그널 라인 EMA 기간 (기본 9일)

    Returns:
        {'macd': MACD 라인, 'signal': 시그널 라인, 'histogram': 히스토그램}
    """
    if len(prices) < slow + signal:
        return None

    # EMA 계산 함수
    def calculate_ema(data: List[float], period: int) -> List[float]:
        ema = []
        multiplier = 2 / (period + 1)

        # 첫 EMA는 SMA로 시작
        sma = sum(data[:period]) / period
        ema.append(sma)

        # 이후 EMA 계산
        for i in range(period, len(data)):
            ema_value = (data[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(ema_value)

        return ema

    # Fast EMA와 Slow EMA 계산
    fast_ema = calculate_ema(prices, fast)
    slow_ema = calculate_ema(prices, slow)

    # MACD 라인 계산 (Fast EMA - Slow EMA)
    # slow EMA 길이에 맞춰 조정
    offset = slow - fast
    macd_line = []
    for i in range(len(slow_ema)):
        macd_value = fast_ema[i + offset] - slow_ema[i]
        macd_line.append(macd_value)

    # Signal 라인 계산 (MACD의 EMA)
    signal_line = calculate_ema(macd_line, signal)

    # Histogram 계산 (MACD - Signal)
    histogram = []
    signal_offset = signal - 1
    for i in range(len(signal_line)):
        hist_value = macd_line[i + signal_offset] - signal_line[i]
        histogram.append(hist_value)

    # 길이 맞추기
    final_macd = macd_line[signal_offset:]

    return {
        'macd': final_macd,
        'signal': signal_line,
        'histogram': histogram
    }


def fallback_result(error_message: str = "데이터를 확보하지 못했습니다.") -> Dict[str, Any]:
    """
    에러 발생 시 반환할 기본 결과

    Args:
        error_message: 에러 메시지

    Returns:
        기본 분석 결과 구조
    """
    return {
        "stock_analysis": {
            "summary": f"주가 흐름 정보를 확보하지 못했습니다. ({error_message})",
            "price_move": {
                "start_price": "unknown",
                "end_price": "unknown",
                "pct_change": "unknown",
            },
            "trend": "sideways",
            "indicators": [
                {
                    "name": "bollinger_band",
                    "value": "unknown",
                    "interpretation": "지표 값을 계산하지 못했습니다.",
                }
            ],
            "risk_notes": ["데이터 소스가 연결되지 않았습니다.", error_message],
            "uncertainty_level": "high",
        }
    }
