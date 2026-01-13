import json

from n6 import node6_stock_analyst, fetch_stock_data, perform_technical_analysis, calculate_bollinger_bands, calculate_rsi, calculate_macd, fallback_result


if __name__ == '__main__':

    # Sample input for testing
    sample_state = {
        "layer1_stock": "AAPL",
        "layer2_buy_date": "2024-03-12",
        "layer2_sell_date": "2024-04-18",
        "layer3_decision_basis": (
            "earnings 기대감으로 매수했지만 실적 발표 후 가이던스가 약했고 "
            "하락 추세 전환으로 손절"
        ),
    }

    try:
        result = node6_stock_analyst(sample_state)
        print("Node6 Stock Analyst Output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error during Node6 Stock Analyst execution:", e)
        print("Using fallback result:")
        print(fallback_result())