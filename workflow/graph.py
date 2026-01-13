from langgraph.graph import StateGraph, END
from state.main_state import MainState
from nodes.n1_loss_input import node1_loss_input
from nodes.n6_stock_analyst import node6_stock_analyst_wrapper
from nodes.n7_news_summarizer import node7_news_summarizer_wrapper
from nodes.n8_loss_analyzer import node8_loss_analyzer
from nodes.n9_learning_pattern import node9_learning_pattern
from nodes.n10_learning_tutor import node10_learning_tutor
from nodes.n4_chat_entry import node4_chat_entry

def build_graph():
    g = StateGraph(MainState)

    g.add_node("N1", node1_loss_input)
    g.add_node("N6", node6_stock_analyst_wrapper)
    g.add_node("N7", node7_news_summarizer_wrapper)
    g.add_node("N8", node8_loss_analyzer)
    g.add_node("N9", node9_learning_pattern)
    g.add_node("N10", node10_learning_tutor)
    g.add_node("N4", node4_chat_entry)

    g.set_entry_point("N1")
    g.add_edge("N1", "N6")
    g.add_edge("N1", "N7")
    g.add_edge("N6", "N8")
    g.add_edge("N7", "N8")
    g.add_edge("N8", "N9")
    g.add_edge("N9", "N10")
    g.add_edge("N10", "N4")
    g.add_edge("N4", END)

    return g.compile()
