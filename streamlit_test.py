import streamlit as st
from streamlit_sortables import sort_items

original_items = ['A', 'B', 'C']
sorted_items = sort_items(original_items, direction='vertical')

st.write(f'Original items: {original_items}')
st.write(f'Sorted items: {sorted_items}')

@st.dialog("確認")
def confirmation_dialog():
    st.write("本当に設定を変更しますか？")
 
    # 「はい」「いいえ」の選択肢を2つのカラムで表示
    col1, col2 = st.columns(2)
 
    with col1:
        if st.button("はい"):
            st.write("設定が変更されました。")
            st.session_state.show_dialog = False  # ダイアログを閉じる
 
    with col2:
        if st.button("いいえ"):
            st.session_state.show_dialog = False  # ダイアログを閉じる

if st.button("button"):
    confirmation_dialog()
