import asyncio
import base64
import io
import os
from datetime import datetime
from random import randint

import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from streamlit.delta_generator import DeltaGenerator
from streamlit_extras.stylable_container import stylable_container
from streamlit_gsheets import GSheetsConnection

RANDOM_APM_VIDEOS = [
    {"data": "https://www.youtube.com/watch?v=dcrR2vs2jKo", "start_time": 21},
    {"data": "https://www.youtube.com/watch?v=S7UM5zdPGpc", "start_time": 9},
    {"data": "https://www.youtube.com/watch?v=sFlAEv8xpjc", "start_time": 13},
    {"data": "https://www.youtube.com/watch?v=Y2Zj84kNEKw", "start_time": 8},
    {"data": "https://www.youtube.com/watch?v=FRVcayal19w"},
    {"data": "https://www.youtube.com/watch?v=6eXG31O9mHU"},
    {"data": "https://www.youtube.com/watch?v=14MwPB9sgJw", "start_time": 7},
    {"data": "https://www.youtube.com/watch?v=oB6LnFYkTzs"},
    {"data": "https://www.youtube.com/watch?v=R3d2m1-4AtY"},
    {"data": "https://www.youtube.com/watch?v=P_EhjbUaKY0"},
    {"data": "https://www.youtube.com/watch?v=ayFYZ-qroXg"},
    {"data": "https://www.youtube.com/watch?v=gekAv8vRQd8", "start_time": 10},
]

# CREDENTIALS = st.cache_resource(ttl=600, show_spinner=False)(
#     service_account.Credentials.from_service_account_info
# )(
#     st.secrets["gcp_service_account"],
#     scopes=[
#         "https://www.googleapis.com/auth/drive",
#     ],
# )
# DRIVE_SERVICE = st.cache_resource(ttl=600, show_spinner=False)(build)(
#     "drive", "v3", credentials=CREDENTIALS
# )
CREDENTIALS = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/drive",
    ],
)
DRIVE_SERVICE = build("drive", "v3", credentials=CREDENTIALS)

PHOTOS_FOLDER_ID = "1nrQyaN5LSraq5I_g1NwdciOfgp0_kwMx"


def download_drive_folder(folder_id: str, folder_path: str) -> None:
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_list = (
        DRIVE_SERVICE.files()
        .list(
            q=f"'{folder_id}' in parents and trashed = false",
            # q="trashed = false",
            fields="files(id, name, mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        )
        .execute()
    )
    for file in file_list.get("files", []):
        if file["mimeType"] == "application/vnd.google-apps.folder":
            download_drive_folder(
                folder_id=file["id"],
                folder_path=os.path.join(folder_path, file["name"]),
            )
        else:
            file_path = os.path.join(folder_path, file["name"])
            if os.path.exists(file_path):
                continue

            request = DRIVE_SERVICE.files().get_media(fileId=file["id"])
            f = io.FileIO(file_path, "wb")
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()


async def countdown(
    container: DeltaGenerator, final_datetime: datetime, infinte_loop: bool = False
) -> None:
    done_once = False
    while infinte_loop or not done_once:
        done_once = True
        timedelta = final_datetime - datetime.now()
        if timedelta.total_seconds() < 0:
            days, hours, minutes, seconds = 0, 0, 0, 0
        else:
            days, hours, minutes, seconds = (
                timedelta.days,
                timedelta.seconds // 3600,
                timedelta.seconds // 60 % 60,
                timedelta.seconds % 60,
            )
        with stylable_container(
            key="countdown",
            css_styles=[
                """{}
            div[data-testid="stMetric"]{
            border: 2px solid rgba(225, 225, 225, 1);
            border-radius: 10px;
            text-align: center;
            }
            div[data-testid="column"]:has(> div[data-testid="stVerticalBlockBorderWrapper"] > div > div > div > div[data-testid="stMetric"]){
            min-width: 0 !important;
            }
            div[data-testid="stMetric"] > label[data-testid="stMetricLabel"]{
            display: flex;
            }
            div[data-testid="stMetric"] > label[data-testid="stMetricLabel"] > div p {
            font-size: 100% !important;
            font-family: cursive;
            }
            div[data-testid="stMetric"] > div[data-testid="stMetricValue"] > div {
            font-size: 50% !important;
            font-family: cursive;
            }""",
            ],
        ):
            days_col, hours_col, minutes_col, seconds_col = container.columns(4)
            days_col.metric("Dies", days)
            hours_col.metric("Hores", hours)
            minutes_col.metric("Minuts", minutes)
            seconds_col.metric("Segons", seconds)

        if infinte_loop:
            await asyncio.sleep(1)


def confirm_no_assistance(
    name_surname: str,
    invitations_df: pd.DataFrame,
    conn: GSheetsConnection,
    play_video: bool = True,
) -> None:
    st.write("Una llàstima que no venguis, ho celebrarem junts un altra moment 🤗")

    if play_video:
        # Queen - The Show Must Go On (2:11)
        st.video("https://www.youtube.com/watch?v=t99KH0TR-J4", start_time=131, autoplay=True)
        # Altres opcions:
        # Que tinguem sort (si em dius adeu) - Lluis Llach
        # st.video("https://www.youtube.com/watch?v=JzW4trGkVds", start_time=11, autoplay=True)
        # - Goodbye My Lover - James Blunt
        # Txarango - Tanca els ulls (a 0:59 o 2:04)
        # Let Her Go de Passenger

    new_entry = pd.DataFrame(
        {
            "Name Surname": [name_surname],
            "Is coming": [False],
        }
    ).set_index(["Name Surname"])
    if name_surname in invitations_df.index:
        invitations_df = invitations_df.drop(name_surname)
    invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
    with st.status("Enviant confirmació de no assitència... 😢") as status:
        conn.update(worksheet="Invitations", data=invitations_df)


@st.experimental_dialog("Acompanyant")
def acompanyant_dialog(
    accompanyant_of: str, invitations_df: pd.DataFrame, conn: GSheetsConnection, index: int = 0
) -> None:
    st.session_state["dialog_open"] = True
    acompanyant_name_surname = st.text_input("Nom i Llinatge (Cognom 😜)", key=f"{accompanyant_of}")
    if acompanyant_name_surname:
        if additional_data(
            name_surname=acompanyant_name_surname,
            invitations_df=invitations_df,
            conn=conn,
            accompanyant_of=accompanyant_of,
        ):
            st.session_state["dialog_open"] = False
            st.rerun()


@st.experimental_dialog("Dades addicionals")
def additional_data_dialog(
    name_surname: str,
    invitations_df: pd.DataFrame,
    conn: GSheetsConnection,
    accompanyant_of: str = "",
) -> None:
    st.session_state["dialog_open"] = True
    sent = additional_data(
        name_surname=name_surname,
        invitations_df=invitations_df,
        conn=conn,
        accompanyant_of=accompanyant_of,
    )
    if sent:
        st.session_state["data_sent"] = True
        st.session_state["dialog_open"] = False
        st.rerun()


def additional_data(
    name_surname: str,
    invitations_df: pd.DataFrame,
    conn: GSheetsConnection,
    accompanyant_of: str = "",
) -> bool:
    if name_surname:
        try:
            exists = invitations_df.loc[name_surname, "Is coming"].all()
            if exists and invitations_df.loc[name_surname, "Is coming"].all():
                st.info(
                    f"Ja comptam amb tu {name_surname} 🥳. Envia de nou en cas de voler modificar colcuna dada."
                )
        except KeyError:
            exists = False

        number_of_baby = number_of_kids = 0
        if not accompanyant_of:
            try:
                default_number_of_baby = invitations_df.loc[name_surname, "Babys"] or 0
                default_number_of_kids = invitations_df.loc[name_surname, "Kids"] or 0
            except (KeyError, ValueError):
                default_number_of_baby = default_number_of_kids = 0
            baby_or_kids = st.radio(
                "Vens amb bebes o fiets? 👶👦",
                options=[False, True],
                format_func=lambda x: "Sí" if x else "No",
                index=int(bool(default_number_of_baby or default_number_of_kids)),
                horizontal=True,
            )
            if baby_or_kids:
                number_of_baby = st.number_input(
                    "Nombre de bebes", min_value=0, max_value=10, value=default_number_of_baby
                )
                number_of_kids = st.number_input(
                    "Nombre de fiets", min_value=0, max_value=10, value=default_number_of_kids
                )
            else:
                number_of_baby = number_of_kids = 0

        with st.form(f"invitation_form_{name_surname}", border=False):
            bus_options = ["No necessit", "Ciutadella", "Maó"]
            bus_format_func = lambda opt: (
                opt if opt != "Maó" else "Maó (possibles aturades altres pobles)"
            )
            try:
                default_source_bus_index = bus_options.index(
                    invitations_df.loc[name_surname, "Source Bus"]
                )
            except (KeyError, ValueError):
                default_source_bus_index = 0
            try:
                default_destination_bus_index = bus_options.index(
                    invitations_df.loc[name_surname, "Destination Bus"]
                )
            except (KeyError, ValueError):
                default_destination_bus_index = 0
            source_bus = st.selectbox(
                "Bus anada",
                bus_options,
                format_func=bus_format_func,
                index=default_source_bus_index,
            )
            destination_bus = st.selectbox(
                "Bus tornada",
                bus_options,
                format_func=bus_format_func,
                index=default_destination_bus_index,
            )
            allergies = st.text_input(
                "Alèrgies, intoleràncies o dietes especials",
                value=invitations_df.loc[name_surname, "Allergies"] if exists else "",
            )
            songs = st.text_area(
                "Cançons que t'agradaria que sonessin",
                value=invitations_df.loc[name_surname, "Songs"] if exists else "",
            )

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
                    "Songs": [songs],
                }
                new_entry = pd.DataFrame(data).set_index(["Name Surname"])
                if exists:
                    invitations_df = invitations_df.drop(name_surname)
                invitations_df = pd.concat([invitations_df, new_entry]).reset_index(drop=False)
                status_placeholder = st.empty()
                with status_placeholder.status("Enviant confirmació...") as status:
                    conn.update(worksheet="Invitations", data=invitations_df)
                status_placeholder.empty()
                st.success("Confirmació enviada. Contam amb voltros! 🥳")
                return True
    return False


@st.cache_data
def static_base64_image(image_filename: str) -> str:
    return base64.b64encode(open(os.path.join(".", "static", image_filename), "rb").read()).decode()


def static_filepath(image_filename: str) -> str:
    return f"./app/static/{image_filename}"


def set_background_image(image_filename: str) -> str:
    return f"""
        <style>
        [data-testid="stAppViewContainer"]{{
        background-image: url("{static_filepath(image_filename)}");
        background-size: cover;
        }}
        [data-testid="stHeader"]{{
        background-color: rgba(0,0,0,0);
        }}
        </style>
        """


def show_maps():
    maps_url = "https://maps.app.goo.gl/8iKreRxjmVgRahaJA"
    st.markdown(
        f"""<a href="{maps_url}">
        <img src="{static_filepath('place_maps_from_mao_creus.png')}" width="100%">
        </a>""",
        unsafe_allow_html=True,
    )
    st.link_button(
        "🗺️ Google Maps 🗺️", url="https://maps.app.goo.gl/8iKreRxjmVgRahaJA", use_container_width=True
    )


def load_data(conn: GSheetsConnection, ttl: int = 0) -> pd.DataFrame:
    invitations_df = conn.read(
        worksheet="Invitations",
        ttl=ttl,
        usecols=[
            "Name Surname",
            "Is coming",
            "Babys",
            "Kids",
            "Accompanyant of",
            "Source Bus",
            "Destination Bus",
            "Allergies",
            "Songs",
        ],
        skip_blank_lines=True,
    )
    invitations_df = invitations_df[invitations_df["Name Surname"].notnull()].set_index(
        ["Name Surname"]
    )
    invitations_df["Is coming"] = invitations_df["Is coming"].astype(bool)
    invitations_df["Babys"] = invitations_df["Babys"].fillna(0).astype(int)
    invitations_df["Kids"] = invitations_df["Kids"].fillna(0).astype(int)
    invitations_df["Accompanyant of"] = invitations_df["Accompanyant of"].fillna("")
    invitations_df["Allergies"] = invitations_df["Allergies"].fillna("")
    invitations_df["Songs"] = invitations_df["Songs"].fillna("")
    return invitations_df


def on_name_surname_change(*args, **kwargs) -> None:
    st.session_state["data_sent"] = False


def hide_toolbar() -> str:
    return """
        <style>
        header[data-testid="stHeader"] {
            visibility: hidden;
            position: fixed;
            height: 0%;
        }
        </style>
        """


def set_image_max_width() -> str:
    return """
        <style>
        img {
            max-width: 100%;
        }
        </style>"""


def general_text_style() -> str:
    return """
        <style>
        div[data-testid="stMarkdownContainer"] {
            font-family: 'Quicksand', sans-serif;
        }</style>"""


st.set_page_config("Iria & Lluís", page_icon="🥂", initial_sidebar_state="collapsed", layout="wide")

st.markdown(
    general_text_style()
    + hide_toolbar()
    + set_image_max_width()
    + set_background_image("background.jpg"),
    unsafe_allow_html=True,
)

with stylable_container(
    key="title",
    css_styles="""
    h1{
        font-size: 60px;
        text-align: center;
        font-weight: 100;
        font-family: cursive;
    }
    p{
        text-align: center;
    }""",
):
    st.title("Iria & Lluís")

    WEDDING_DATETIME = datetime(2024, 9, 28, 12, 0, 0)
    st.write("28 setembre 2024")

    countdown_placeholder = st.empty()
    asyncio.run(
        countdown(
            container=countdown_placeholder, final_datetime=WEDDING_DATETIME, infinte_loop=False
        )
    )

with st.spinner("Carregant imatges..."):
    download_drive_folder(folder_id=PHOTOS_FOLDER_ID, folder_path="./static/private")

with stylable_container(
    key="introduction",
    css_styles="""
    > div[data-testid="stHorizontalBlock"]{
            display: flex;
            align-items: center !important;
            justify-content: center !important;
    }""",
):
    left_col, right_col = st.columns([2, 1])
    left_col.image("./static/private/IMG_20240408_112715.jpg", width=700)
    with right_col:
        st.markdown(
            "<span style='font-family: cursive; font-size: 30px;'>Aço es una frase super cuqui per tothom es dia que mus casam :D</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """<a href='#c15c19bd'><div class="row-widget stButton" data-testid="stButton"><button kind="secondary" data-testid="baseButton-secondary" class="st-emotion-cache-1umgz6k ef3psqc12" style="background-color: #dcedc1;"><div data-testid="stMarkdownContainer" class="st-emotion-cache-j6qv4b e1nzilvr4"><p><span style="color: rgb(49, 51, 63);">Confirmar assistència</span></p></div></button></div></a>""",
            unsafe_allow_html=True,
        )

st.header("🚗🚌 Com arribar a Rafal Nou? 🚑🚓")

left_col, right_col = st.columns([1, 1])
with left_col:
    st.write("Bla blah" * 100)

with right_col:
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
    else:
        additional_data_dialog(name_surname=name_surname, invitations_df=invitations_df, conn=conn)

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
                    additional_data(
                        name_surname=acompanyant,
                        invitations_df=invitations_df,
                        conn=conn,
                        accompanyant_of=name_surname,
                    )
                if right_col.button(":red[S'ho perdrà 😢]"):
                    confirm_no_assistance(
                        name_surname=acompanyant, invitations_df=invitations_df, conn=conn
                    )
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
    st.info("Modifica les dades enviades tantes vegades com vulguis tornant a omplir el formulari")
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ", autoplay=True)
    st.balloons()
    st.session_state["data_sent"] = False

left_col, _, right_col = st.columns([2, 1, 1])
left_col.caption("Made with ❤️ by Iria and Lluis")
right_col.caption("Background by [Freepik](www.freepik.es)")

# MUST BE AT THE END
if not "dialog_open" in st.session_state or not st.session_state["dialog_open"]:
    if "dialog_open" in st.session_state:
        del st.session_state["dialog_open"]
    else:
        asyncio.run(
            countdown(
                container=countdown_placeholder, final_datetime=WEDDING_DATETIME, infinte_loop=True
            )
        )
