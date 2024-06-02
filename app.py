import base64
from random import randint
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

RANDOM_APM_VIDEOS = [
    {
        "data": "https://www.youtube.com/watch?v=dcrR2vs2jKo", "start_time": 21
    },
    {
        "data": "https://www.youtube.com/watch?v=S7UM5zdPGpc", "start_time": 9
    },
    {
        "data": "https://www.youtube.com/watch?v=sFlAEv8xpjc", "start_time": 13
    },
    {
        "data": "https://www.youtube.com/watch?v=Y2Zj84kNEKw", "start_time": 8
    },
    {
        "data": "https://www.youtube.com/watch?v=FRVcayal19w"
    },
    {
        "data": "https://www.youtube.com/watch?v=6eXG31O9mHU"
    },
    {
        "data": "https://www.youtube.com/watch?v=14MwPB9sgJw", "start_time": 7
    },
    {
        "data": "https://www.youtube.com/watch?v=oB6LnFYkTzs"
    },
    {
        "data": "https://www.youtube.com/watch?v=R3d2m1-4AtY"
    },
    {
        "data": "https://www.youtube.com/watch?v=P_EhjbUaKY0"
    },
    {
        "data": "https://www.youtube.com/watch?v=ayFYZ-qroXg"
    },
    {
        "data": "https://www.youtube.com/watch?v=gekAv8vRQd8", "start_time": 10
    }
]

def confirm_no_assistance(name_surname: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, play_video: bool = True) -> None:
    st.write("Una llàstima que no venguis, ho celebrarem junts un altra moment 🤗")

    if play_video:
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
    if name_surname in invitations_df.index:
        invitations_df = invitations_df.drop(name_surname)
    invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
    with st.status("Enviant confirmació de no assitència... 😢") as status:
        conn.update(
            worksheet="Invitations",
            data=invitations_df
        )

@st.experimental_dialog("Acompanyant")
def acompanyant_dialog(accompanyant_of: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, index: int = 0) -> None:
    acompanyant_name_surname = st.text_input("Nom i Llinatge (Cognom 😜)", key=f"{accompanyant_of}")
    if acompanyant_name_surname:
        if additional_data(name_surname=acompanyant_name_surname, invitations_df=invitations_df, conn=conn, accompanyant_of=accompanyant_of):
            st.rerun()

@st.experimental_dialog("Dades addicionals")
def additional_data_dialog(name_surname: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, accompanyant_of: str = "") -> None:
    sent = additional_data(name_surname=name_surname, invitations_df=invitations_df, conn=conn, accompanyant_of=accompanyant_of)
    if sent:
        st.session_state["data_sent"] = True
        st.rerun()

def additional_data(name_surname: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, accompanyant_of: str = "") -> bool:
    if name_surname:
        try:
            exists = invitations_df.loc[name_surname, "Is coming"].all()
            if exists and invitations_df.loc[name_surname, "Is coming"].all():
                st.info(f"Ja comptam amb tu {name_surname} 🥳. Envia de nou en cas de voler modificar colcuna dada.")
        except KeyError:
            exists = False

        number_of_baby = number_of_kids = 0
        if not accompanyant_of:
            try:
                default_number_of_baby = invitations_df.loc[name_surname, "Babys"] or 0
                default_number_of_kids = invitations_df.loc[name_surname, "Kids"] or 0
            except (KeyError, ValueError):
                default_number_of_baby = default_number_of_kids = 0
            baby_or_kids = st.radio("Vens amb bebes o fiets? 👶👦", options=[False, True], format_func=lambda x: "Sí" if x else "No", index=int(bool(default_number_of_baby or default_number_of_kids)), horizontal=True)
            if baby_or_kids:
                number_of_baby = st.number_input("Nombre de bebes", min_value=0, max_value=10, value=default_number_of_baby)
                number_of_kids = st.number_input("Nombre de fiets", min_value=0, max_value=10, value=default_number_of_kids)
            else:
                number_of_baby = number_of_kids = 0

        with st.form(f"invitation_form_{name_surname}", border=False):
            bus_options = ["No necessit", "Ciutadella", "Maó"]
            bus_format_func = lambda opt: opt if opt != "Maó" else "Maó (possibles aturades altres pobles)"
            try:
                default_source_bus_index = bus_options.index(invitations_df.loc[name_surname, "Source Bus"])
            except (KeyError, ValueError):
                default_source_bus_index = None
            try:
                default_destination_bus_index = bus_options.index(invitations_df.loc[name_surname, "Destination Bus"])
            except (KeyError, ValueError):
                default_destination_bus_index = None
            source_bus = st.selectbox("Bus anada", bus_options, format_func=bus_format_func, index=default_source_bus_index)
            destination_bus = st.selectbox("Bus tornada", bus_options, format_func=bus_format_func, index=default_destination_bus_index)
            allergies = st.text_input("Alèrgies o intoleràncies", value=invitations_df.loc[name_surname, "Allergies"] if exists else "")
            songs = st.text_area("Cançons que t'agradaria que sonessin", value=invitations_df.loc[name_surname, "Songs"] if exists else "")

            submit = st.form_submit_button("Enviar")

            if submit:
                data = {
                    "Name Surname": [name_surname],
                    "Is coming": [True],
                    "Babys": [number_of_baby],
                    "Kids": [number_of_kids],
                    "Accompanyant of": [accompanyant_of],
                    "Source Bus": [source_bus],
                    "Destination Bus": [destination_bus],
                    "Allergies": [allergies],
                    "Songs": [songs]
                }
                new_entry = pd.DataFrame(data).set_index(["Name Surname"])
                if exists:
                    invitations_df = invitations_df.drop(name_surname)
                invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
                status_placeholder = st.empty()
                with status_placeholder.status("Enviant confirmació...") as status:
                    conn.update(
                        worksheet="Invitations",
                        data=invitations_df
                    )
                status_placeholder.empty()
                st.success("Confirmació enviada. Contam amb voltros! 🥳")
                return True

@st.cache_data
def base64_image(image_file: str) -> str:
    return base64.b64encode(open(image_file, "rb").read()).decode()

def show_maps():
    maps_url = "https://maps.app.goo.gl/8iKreRxjmVgRahaJA"
    image_data = base64_image("statics/place_maps_with_crosses.png")
    st.markdown(
        f"""<a href="{maps_url}">
        <img src="data:image/png;base64,{image_data}" width="100%">
        </a>""",
        unsafe_allow_html=True
    )
    st.link_button("🗺️ Google Maps 🗺️", url="https://maps.app.goo.gl/8iKreRxjmVgRahaJA", use_container_width=True)
    
def load_data(conn: GSheetsConnection, ttl: int = 0) -> pd.DataFrame:
    invitations_df = conn.read(
        worksheet="Invitations",
        ttl=ttl,
        usecols=["Name Surname", "Is coming", "Babys", "Kids", "Accompanyant of", "Source Bus", "Destination Bus", "Allergies", "Songs"],
        skip_blank_lines=True,
    )
    invitations_df = invitations_df[invitations_df["Name Surname"].notnull()].set_index(["Name Surname"])
    invitations_df["Is coming"] = invitations_df["Is coming"].astype(bool)
    invitations_df["Babys"] = invitations_df["Babys"].astype(int)
    invitations_df["Kids"] = invitations_df["Kids"].astype(int)
    return invitations_df

def on_name_surname_change(*args, **kwargs) -> None:
    st.session_state["data_sent"] = False

st.set_page_config("Confirma assistència", page_icon="✍️", initial_sidebar_state="collapsed", layout="centered")

st.header("🚗🚌 Com arribar a Rafal Nou? 🚑🚓")
show_maps()

st.title("Confirma assistència")

status_placeholder = st.empty()
with status_placeholder.status("Carregant dades...") as status:
    conn = st.connection("gsheets", type=GSheetsConnection)

    invitations_df = load_data(conn=conn, ttl=0)
    status.update(label="Dades carregades! 🎉", state="complete", expanded=False)
status_placeholder.empty()

st.subheader("Qui ets? 🤔")
name_surname = st.text_input("Nom i Llinatge (Cognom 😜)", on_change=on_name_surname_change)

left_col, right_col = st.columns([2, 1])
if left_col.button(":green[Compta amb jo! 🙌]", use_container_width=True):
    if not name_surname:
        st.error("Necessites un nom i un cognom 😅")
        sent = False
    else:
        sent = additional_data_dialog(name_surname=name_surname, invitations_df=invitations_df, conn=conn)

if right_col.button(":red[M'ho perdré 😢]", use_container_width=True):
    if not name_surname:
        st.error("Necessites un nom i un cognom 😅")
    else:
        confirm_no_assistance(name_surname=name_surname, invitations_df=invitations_df, conn=conn)

st.divider()
st.subheader("🧑‍🤝‍🧑 Acompanyants 🧑‍🤝‍🧑")
if name_surname:
    acompanyants = invitations_df[invitations_df["Accompanyant of"] == name_surname]
    if not acompanyants.empty:
        for acompanyant in acompanyants.index:
            with st.container(border=True):
                left_col, middle_col, right_col = st.columns(3)
                left_col.write(f"#### {acompanyant}")
                with middle_col.popover(":green[Compta amb ell/a! 🙌]", use_container_width=True):
                    additional_data(name_surname=acompanyant, invitations_df=invitations_df, conn=conn, accompanyant_of=name_surname)
                if right_col.button(":red[S'ho perdrà 😢]"):
                    confirm_no_assistance(name_surname=acompanyant, invitations_df=invitations_df, conn=conn)
else:
    st.info("Introdueix es teu nom i llinatge per poder afegir els acompanyants")
if st.button("➕ Afegir acompanyant", use_container_width=True, disabled=not name_surname):
    acompanyant_dialog(accompanyant_of=name_surname, invitations_df=invitations_df, conn=conn)

st.divider()
if st.button("😹 Video random d'APM 😹", use_container_width=True):
    st.info("Clickeu de nou per veure un altre")
    video_random = RANDOM_APM_VIDEOS[randint(0, len(RANDOM_APM_VIDEOS) - 1)]
    st.video(**video_random, autoplay=True)

if "data_sent" not in st.session_state:
    st.session_state["data_sent"] = False

if st.session_state["data_sent"]:
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", autoplay=True)
    st.balloons()
    st.session_state["data_sent"] = False
