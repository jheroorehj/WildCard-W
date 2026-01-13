import { InvestmentFormData, AnalysisResult } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const analyzeInvestmentLoss = async (
  data: InvestmentFormData
): Promise<AnalysisResult> => {
  const response = await fetch(`${API_BASE_URL}/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      layer1_stock: data.stockName,
      layer2_buy_date: data.buyDate,
      layer2_sell_date: data.sellDate,
      layer3_decision_basis: data.decisionBasis.join(", "),
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
