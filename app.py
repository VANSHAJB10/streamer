
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Spreadsheet Dashboard",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------
# CONFIGURATION: All four tabs in your Google Sheet
# --------------------------------------------------

SPREADSHEET_ID = "1ab1ZDtxUXgMbDjmHCFZhTIRDV1a3yzi7lDA7-PC40MU"

SPREADSHEETS = {
    "Products": 1397139536,
    "Transactions": 1590441917,
    "Inventory": 831988835,
    "TestData": 1737675647,
}

# --------------------------------------------------
# GOOGLE SHEETS AUTHENTICATION
# --------------------------------------------------

@st.cache_resource
def get_google_client():
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(credentials)


def get_worksheet(gid):
    spreadsheet = get_google_client().open_by_key(
        SPREADSHEET_ID
    )

    for worksheet in spreadsheet.worksheets():
        if worksheet.id == int(gid):
            return worksheet

    raise ValueError(
        f"Could not find worksheet with GID {gid}."
    )


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

def worksheet_to_dataframe(worksheet):
    values = worksheet.get_all_values()

    if not values:
        return pd.DataFrame()

    headers = values[0]

    if not any(str(header).strip() for header in headers):
        raise ValueError(
            "The first row must contain column headers."
        )

    # Make blank column names usable
    headers = [
        str(header).strip() or f"Column {i + 1}"
        for i, header in enumerate(headers)
    ]

    # Keep rows the same width as the header
    rows = [
        row[:len(headers)]
        + [""] * max(0, len(headers) - len(row))
        for row in values[1:]
    ]

    return pd.DataFrame(rows, columns=headers)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("📊 Dashboard")
st.sidebar.caption("Google Sheets Manager")

selected_sheet = st.sidebar.radio(
    "Select a spreadsheet",
    list(SPREADSHEETS.keys()),
)

gid = SPREADSHEETS[selected_sheet]

st.sidebar.divider()

st.sidebar.markdown(
    f"[🔗 Open {selected_sheet} in Google Sheets]"
    f"(https://docs.google.com/spreadsheets/d/"
    f"{SPREADSHEET_ID}/edit?gid={gid}#gid={gid})"
)

# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------

st.title(f"📄 {selected_sheet}")

st.caption(
    "Edit cells directly in the table, then click Save Changes."
)

try:
    worksheet = get_worksheet(gid)
    df = worksheet_to_dataframe(worksheet)

    # Empty worksheet handling
    if df.empty:
        st.warning(
            "This worksheet has no data yet. "
            "Add a header row in Google Sheets first."
        )
        st.stop()

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", len(df))
    col2.metric("Columns", len(df.columns))
    col3.metric("Worksheet", selected_sheet)

    st.divider()

    # Editable table
    edited_df = st.data_editor(
        df,
        key=f"editor_{gid}",
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "You can edit cells, add rows, or delete rows "
        "using the table controls."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💾 Save Changes",
            type="primary",
            width="stretch",
        ):
            # Read the current table before saving
            worksheet = get_worksheet(gid)

            # Prepare the edited data
            data = [
                edited_df.columns.tolist()
            ]

            for row in edited_df.itertuples(
                index=False,
                name=None,
            ):
                data.append([
                    "" if pd.isna(value) else value
                    for value in row
                ])

            # Ensure the sheet has enough rows and columns
            worksheet.resize(
                rows=max(len(data), 1),
                cols=max(len(edited_df.columns), 1),
            )

            # Write changes back to the selected tab
            worksheet.update(
                range_name="A1",
                values=data,
                value_input_option="USER_ENTERED",
            )

            st.success(
                f"✅ {selected_sheet} saved successfully!"
            )

            st.rerun()

    with col2:
        if st.button(
            "🔄 Discard & Reload",
            width="stretch",
        ):
            st.rerun()

    st.divider()

    st.markdown(
        f"**Editing:** {selected_sheet}  \n"
        "Changes are written to the selected Google "
        "Sheets tab when you click Save Changes."
    )

except Exception as e:
    st.error("Unable to load or update this worksheet.")
    st.code(str(e))

    st.info(
        "Verify your Google service account credentials "
        "and confirm that its email has Editor access "
        "to the spreadsheet."
    )
