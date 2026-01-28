import streamlit as st
import pandas as pd
import datetime
import requests
import os

# -----------------------------
# CONFIG
# -----------------------------
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID"
PERMANENT_TOKEN = "YOUR_PERMANENT_TOKEN"
TO_NUMBER = "NUMBER_HERE"

if not os.path.exists("uploads"):
    os.makedirs("uploads")


# -----------------------------
# WHATSAPP SEND FUNCTIONS
# -----------------------------
def send_whatsapp_text(message: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {PERMANENT_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "text",
        "text": {"body": message},
    }

    r = requests.post(url, json=payload, headers=headers)
    return r.json()


def send_whatsapp_file(file_path: str):
    # Step 1 — Upload file
    upload_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/media"

    headers = {"Authorization": f"Bearer {PERMANENT_TOKEN}"}

    files = {"file": open(file_path, "rb")}
    data = {"messaging_product": "whatsapp", "type": "document"}

    upload_res = requests.post(
        upload_url, headers=headers, files=files, data=data
    ).json()

    if "id" not in upload_res:
        return {"error": upload_res}

    media_id = upload_res["id"]

    # Step 2 — Send file using media_id
    send_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "document",
        "document": {"id": media_id},
    }

    headers = {
        "Authorization": f"Bearer {PERMANENT_TOKEN}",
        "Content-Type": "application/json",
    }

    r = requests.post(send_url, json=payload, headers=headers)
    return r.json()


# ======================================================
# STREAMLIT UI
# ======================================================
st.set_page_config(
    page_title="Order Portal", layout="wide", page_icon=":material/orders:"
)

st.title("🛒 Dwarkadhish Retail Order Portal")
st.space()
st.subheader(
    "Select how you want to submit your order:",
)
mode = st.radio(
    "",
    ["📋 Table Entry", "📝 Text Entry", "📤 Upload Files"],
    index=0,
    horizontal=True,
    width="stretch",
)

st.write("---")

# ======================================================
# 1️⃣ TABLE ENTRY
# ======================================================
if mode == "📋 Table Entry":
    st.header("📋 Enter Order Table")

    retailer = st.text_input("Retailer Name")

    columns = ["Item", "Quantity", "Remarks"]
    default_table = pd.DataFrame([["", 1, ""]], columns=columns)

    table_data = st.data_editor(default_table, num_rows="dynamic")

    if st.button("Submit Order"):
        if not retailer:
            st.error("Please enter retailer name.")
        else:
            # Save table → Excel
            filename = f"uploads/order_{retailer}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            table_data.to_excel(filename, index=False)

            # Send file via WhatsApp
            result = send_whatsapp_file(filename)

            # UI Confirmation
            table_data["Retailer"] = retailer
            table_data["Timestamp"] = datetime.datetime.now()

            st.subheader("Order Summary")
            st.dataframe(table_data)

            st.success("Order captured & sent to WhatsApp!")
            st.json(result)


# ======================================================
# 2️⃣ TEXT ENTRY
# ======================================================
elif mode == "📝 Text Entry":
    st.header("📝 Enter Order Text")

    retailer = st.text_input("Retailer Name")
    message_text = st.text_area("Type your order (like WhatsApp message):", height=200)

    if st.button("Submit Order"):
        if not retailer:
            st.error("Retailer name is required.")
        elif not message_text.strip():
            st.error("Please enter your message.")
        else:
            message = f"New Order from {retailer}:\n\n{message_text}"

            # Send to WhatsApp
            result = send_whatsapp_text(message)

            st.subheader("Order Summary")
            st.write("**Retailer:**", retailer)
            st.write("**Order Text:**")
            st.write(message_text)

            st.success("Order submitted & sent to WhatsApp!")
            st.json(result)


# ======================================================
# 3️⃣ UPLOAD FILES
# ======================================================
elif mode == "📤 Upload Files":
    st.header("📤 Upload Order Files")

    retailer = st.text_input("Retailer Name")
    files = st.file_uploader(
        "Upload any files (Excel, PDF, Word, Images):",
        type=["xlsx", "xls", "pdf", "docx", "jpg", "jpeg", "png", "jfif"],
        accept_multiple_files=True,
    )

    if st.button("Submit Order"):
        if not retailer:
            st.error("Retailer name is required.")
        elif not files:
            st.error("Please upload at least one file.")
        else:
            st.subheader("Uploaded Order Files:")

            results = []

            for file in files:
                file_path = f"uploads/{file.name}"
                with open(file_path, "wb") as out:
                    out.write(file.read())

                # Send WhatsApp
                result = send_whatsapp_file(file_path)
                results.append({file.name: result})

                # show file info
                st.write(f"- **{file.name}** sent ✔")

            st.success("All files sent to WhatsApp!")
            st.json(results)
