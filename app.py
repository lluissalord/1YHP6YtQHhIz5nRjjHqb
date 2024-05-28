import numpy as np
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config("Confirma assistència", page_icon="✍️", initial_sidebar_state="collapsed", layout="centered")

def confirm_no_assistance(name_surname: str, invitations_df: pd.DataFrame, conn: GSheetsConnection) -> None:
    st.write("Una llàstima que no venguis, ho celebrarem junts un altra moment 🤗")

    # Queen - The Show Must Go On (2:11)
    st.video("https://www.youtube.com/watch?v=t99KH0TR-J4", start_time=131, autoplay=True)
    # Altres opcions:
    # Que tinguem sort (si em dius adeu) - Lluis Llach
    # st.video("https://www.youtube.com/watch?v=JzW4trGkVds", start_time=11, autoplay=True)
    #- Goodbye My Lover - James Blunt
    # Txarango - Tanca els ulls (a 0:59 o 2:04)
    # Let Her Go de Passenger

    new_entry = pd.DataFrame({
        "Name Surname": [name_surname],
        "Is coming": [False],
    }).set_index(["Name Surname"])
    invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
    with st.status("Enviant confirmació de no assitència... 😢"):
        conn.update(
            worksheet="Invitations",
            data=invitations_df
        )

def additional_data(name_surname: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, accompanyant_of: str = "") -> bool:
    if name_surname:
        try:
            exists = invitations_df.loc[name_surname, "Is coming"].all()
            if exists and invitations_df.loc[name_surname, "Is coming"].all():
                st.info(f"Ja comptam amb tu {name_surname} 🥳. Envia de nou en cas de voler modificar colcuna dada.")
        except KeyError:
            exists = False

        with st.form(f"invitation_form_{name_surname}"):
            source_bus = st.selectbox("Bus anada", ["No necessit", "Ciutadella", "Maó"], format_func=lambda opt: opt if opt != "Maó" else "Maó (possibles aturades altres pobles)")
            destination_bus = st.selectbox("Bus tornada", ["No necessit", "Ciutadella", "Maó"], format_func=lambda opt: opt if opt != "Maó" else "Maó (possibles aturades altres pobles)")
            allergies = st.text_input("Alèrgies o intoleràncies", value=invitations_df.loc[name_surname, "Allergies"] if exists else "")
            songs = st.text_area("Cançons que t'agradaria que sonessin", value=invitations_df.loc[name_surname, "Songs"] if exists else "")

            submit = st.form_submit_button("Enviar")

            if submit:
                new_entry = pd.DataFrame({
                    "Name Surname": [name_surname],
                    "Is coming": [True],
                    "Accompanyants of": [accompanyant_of],
                    "Source Bus": [source_bus],
                    "Destination Bus": [destination_bus],
                    "Allergies": [allergies],
                    "Songs": [songs]
                }).set_index(["Name Surname"])
                invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
                with st.status("Enviant confirmació..."):
                    conn.update(
                        worksheet="Invitations",
                        data=invitations_df
                    )
                st.success("Confirmació enviada. Contam amb voltros! 🥳")
                st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", autoplay=True)
                return True
        

with st.status("Carregant dades...") as status:
    # Create a connection object.
    conn = st.connection("gsheets", type=GSheetsConnection)

    invitations_df = conn.read(
        worksheet="Invitations",
        ttl=0,
        usecols=["Name Surname", "Is coming", "Accompanyant of", "Source Bus", "Destination Bus", "Allergies", "Songs"],
        skip_blank_lines=True,
    )
    invitations_df = invitations_df[invitations_df["Name Surname"].notnull()].set_index(["Name Surname"])
    invitations_df["Is coming"] = invitations_df["Is coming"].astype(bool)
    status.update(label="Dades carregades! 🎉", state="complete")


name_surname = st.text_input("Nom i Llinatge (Cognom 😜)")

left_col, right_col = st.columns([2, 1])
with left_col.popover("Compta amb jo! 🙌", use_container_width=True, disabled=not name_surname):
    sent = additional_data(name_surname=name_surname, invitations_df=invitations_df, conn=conn)
if sent:
    st.balloons()

if right_col.button("M'ho perdre 😢", use_container_width=True, disabled=not name_surname):
    confirm_no_assistance(name_surname=name_surname, invitations_df=invitations_df, conn=conn)