from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=30).run()
assert not at.exception, at.exception
for level in ("Easy", "Medium", "Hard"):
    at.sidebar.radio[0].set_value(level).run()
    at.selectbox[0].set_value("e4" if level == "Easy" else at.selectbox[0].options[0]).run()
    assert not at.exception, at.exception
board = at.session_state.board
assert len(board.move_stack) == 6, board.move_stack  # 3 player + 3 AI plies
at.sidebar.button[0].click().run()
assert len(at.session_state.board.move_stack) == 0
print("ok:", board.fen())
