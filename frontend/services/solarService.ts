import { InvestmentFormData, AnalysisResult } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const analyzeInvestmentLoss = async (
  data: InvestmentFormData
): Promise<AnalysisResult> => {
  const latestStock = data.stocks[data.stocks.length - 1];
  const [buyDate, sellDate] =
    latestStock?.period === "직접 입력" && latestStock.customPeriod
      ? latestStock.customPeriod.split(" ~ ").map(value => value.trim())
      : ["", ""];

  const response = await fetch(`${API_BASE_URL}/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      layer1_stock: latestStock?.name || "",
      layer2_buy_date: buyDate || "",
      layer2_sell_date: sellDate || "",
      position_status: latestStock?.status || "holding",
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

  return response.json();
};
