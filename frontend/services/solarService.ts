import { InvestmentFormData, AnalysisResult } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const analyzeInvestmentLoss = async (
  data: InvestmentFormData
): Promise<AnalysisResult> => {
  // Transform stocks array to comma-separated string
  const stockNames = data.stocks.map(s => s.name).join(", ");

  // Calculate overall date range (earliest buy, latest sell)
  const allDates = data.stocks.flatMap(s => {
    if (s.period === "직접 입력" && s.customPeriod) {
      const [start, end] = s.customPeriod.split(" ~ ");
      return [start, end].filter(Boolean);
    }
    return [];
  });

  const buyDate = allDates.length > 0 ?
    allDates.reduce((earliest, date) => date < earliest ? date : earliest) :
    "";
  const sellDate = allDates.length > 0 ?
    allDates.reduce((latest, date) => date > latest ? date : latest) :
    "";

  const response = await fetch(`${API_BASE_URL}/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      layer1_stock: data.stockName,
      layer2_buy_date: data.buyDate,
      layer2_sell_date: data.sellDate,
      position_status: data.positionStatus,
      layer3_decision_basis: data.decisionBasis.join(", "),
      // Optional: Send full stock details in metadata for future use
      metadata: {
        stocks: data.stocks
      }
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

export const chatWithAnalyst = async (
  history: { role: string; content: string }[],
  message: string
) => {
  const response = await fetch(`${API_BASE_URL}/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      history,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  const result = await response.json();
  return result.message || "";
};
