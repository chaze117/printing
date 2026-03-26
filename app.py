import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Sütikiszúró rendelő", layout="wide")

# -----------------------
# INIT
# -----------------------
if "cart" not in st.session_state:
    st.session_state.cart = []

# -----------------------
# LOAD DATA
# -----------------------
with open("products.json", "r", encoding="utf-8") as f:
    data = json.load(f)

items = data["items"]

# -----------------------
# HELPERS
# -----------------------
def is_new(item):
    if "new_until" not in item:
        return False
    try:
        expiry = datetime.fromisoformat(item["new_until"])
        return datetime.now() <= expiry
    except:
        return False

# -----------------------
# UI
# -----------------------
st.title("🍪 Sütikiszúró rendelő")


# kategóriák (egyediek)
categories = sorted(set(i["category"] for i in items.values()))

# -----------------------
# TABS
# -----------------------
tabs = st.tabs(categories)

for tab, category in zip(tabs, categories):
    with tab:

        filtered = [
            i for i in items.values()
            if i["category"] == category
        ]

        # új cuccok előre
        filtered.sort(key=lambda x: not is_new(x))

        cols = st.columns(5)

        for i, item in enumerate(filtered):
            with cols[i % 5]:
                st.image(f"images/{item['img']}", width="stretch")

                name_html = f"<b>{item['name']}</b>"
                #size_html = f"<div style='font-size:14px;>Méret: {item['size']} cm</div>"

                if is_new(item):
                    days_left = (
                        datetime.fromisoformat(item["new_until"]) - datetime.now()
                    ).days

                    badge_html = f"""
                    <span style="
                        background-color:#2ec429;
                        color:white;
                        padding:2px 6px;
                        border-radius:6px;
                        font-size:12px;
                        margin-left:8px;
                    ">
                        ÚJ
                    </span>
                    """
                else:
                    # 👇 HELY FENNTARTÁSA
                    badge_html = """
                    <span style="
                        visibility:hidden;
                        padding:2px 6px;
                        margin-left:8px;
                        font-size:12px;
                    ">
                        placeholder
                    </span>
                    """

                st.markdown(
                    f"""
                    <div style="
                        display:flex;
                        align-items:center;
                        height:28px;   /* 👈 fix magasság */
                    ">
                        {name_html}
                        {badge_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                

                qty = st.number_input(
                    "Darab", 1, 10, 1,
                    key=f"{category}_{item['name']}"
                )

                if st.button(
                    "Kérem",
                    key=f"{category}_{item['name']}_btn"
                ):
                    # Ellenőrizzük, hogy már van-e a kosárban
                    found = False
                    for cart_item in st.session_state.cart:
                        if cart_item["name"] == item["name"]:
                            cart_item["qty"] += qty
                            found = True
                            break
                    if not found:
                        # Ha nincs, hozzáadjuk újként
                        st.session_state.cart.append({
                            "name": item["name"],
                            "qty": qty
                        })

# -----------------------
# CART
# -----------------------
st.sidebar.title("🛒 Kosár")

if st.session_state.cart:
    for i, c in enumerate(st.session_state.cart):
        col1, col2 = st.sidebar.columns([5, 1])

        with col1:
            st.write(f"{c['name']} x{c['qty']}")
        with col2:
            b_css = f"""
                .st-key-remove_{i} p {{
                    color: red;
                    padding-top: -10px;
                    margin-top: -10px
                }}
                """

            st.html(f"<style>{b_css}</style>")
            if st.button("❌", key=f"remove_{i}",type="tertiary"):
                st.session_state.cart.pop(i)
                st.rerun()
    total = sum(item["qty"] for item in st.session_state.cart)
    st.sidebar.write(f"Összes darab: {total}")
    if st.sidebar.button("Kosár ürítése"):
        st.session_state.cart = []
        st.rerun()
else:
    st.sidebar.write("Üres a kosár")

name = st.sidebar.text_input("Neved")

# -----------------------
# ORDER SUBMIT
# -----------------------
if st.sidebar.button("Leadom rendelést"):
    if not name:
        st.sidebar.error("Add meg a neved!")
    elif not st.session_state.cart:
        st.sidebar.error("Üres a kosár!")
    else:
        rows = []

        for item in st.session_state.cart:
            rows.append({
                "Idő": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Név": name,
                "Termék": item["name"],
                "Darab": item["qty"]
            })

        df_new = pd.DataFrame(rows)

        if os.path.exists("orders.csv"):
            df_old = pd.read_csv("orders.csv")
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new

        df.to_csv("orders.csv", index=False)

        st.sidebar.success("Rendelés leadva!")
        st.session_state.cart = []

# -----------------------
# ADMIN PANEL
# -----------------------
st.sidebar.markdown("---")
if st.sidebar.checkbox("Admin nézet"):

    if os.path.exists("orders.csv"):
        df = pd.read_csv("orders.csv")

        st.subheader("📋 Összes rendelés")
        st.dataframe(df)

        st.subheader("📊 Összesítés (nyomtatáshoz)")
        summary = df.groupby("Termék")["Darab"].sum().reset_index()
        st.dataframe(summary)

    else:
        st.write("Még nincs rendelés")