import os
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


st.set_page_config(
    page_title="Vehicle Damage Inspection",
    layout="wide",
)


def _init_state() -> None:
    st.session_state.setdefault("api_base_url", DEFAULT_API_BASE_URL)
    st.session_state.setdefault("token", "")
    st.session_state.setdefault("current_user", None)


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    authenticated: bool = True,
) -> dict[str, Any] | None:
    url = f"{st.session_state.api_base_url.rstrip('/')}{path}"
    headers = _headers() if authenticated else None
    try:
        response = requests.request(
            method,
            url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None

    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        st.error(f"{response.status_code}: {detail}")
        return None

    return response.json()


def api_file(path: str) -> bytes | None:
    url = f"{st.session_state.api_base_url.rstrip('/')}{path}"
    try:
        response = requests.get(url, headers=_headers(), timeout=30)
    except requests.RequestException as exc:
        st.error(f"Download failed: {exc}")
        return None

    if not response.ok:
        st.error(f"{response.status_code}: {response.text}")
        return None
    return response.content


def login_panel() -> bool:
    with st.sidebar:
        st.text_input("API Base URL", key="api_base_url")
        st.divider()

        if st.session_state.current_user:
            user = st.session_state.current_user
            st.write(f"Signed in as {user['full_name']}")
            st.caption(user["email"])
            if st.button("Sign Out", use_container_width=True):
                st.session_state.token = ""
                st.session_state.current_user = None
                st.rerun()
            return True

        with st.form("login_form"):
            email = st.text_input("Email", value="inspector@example.com")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)

        if submitted:
            response = api_json(
                "POST",
                "/api/auth/login",
                data={"username": email, "password": password},
                authenticated=False,
            )
            if response:
                st.session_state.token = response["data"]["access_token"]
                st.session_state.current_user = response["data"]["user"]
                st.rerun()

    st.title("Vehicle Damage Inspection")
    st.info("Sign in from the sidebar to open the inspection dashboard.")
    return False


def dataframe_from_items(items: list[dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)


def load_vehicles() -> list[dict[str, Any]]:
    response = api_json("GET", "/api/vehicles", params={"page_size": 100})
    return response["data"]["items"] if response else []


def load_inspections() -> list[dict[str, Any]]:
    response = api_json("GET", "/api/inspections", params={"page_size": 100})
    return response["data"]["items"] if response else []


def load_reports() -> list[dict[str, Any]]:
    response = api_json("GET", "/api/reports", params={"page_size": 100})
    return response["data"]["items"] if response else []


def render_overview() -> None:
    vehicles = load_vehicles()
    inspections = load_inspections()
    reports = load_reports()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vehicles", len(vehicles))
    col2.metric("Inspections", len(inspections))
    col3.metric("Reports", len(reports))
    col4.metric(
        "Completed",
        sum(1 for inspection in inspections if inspection["status"] == "completed"),
    )

    if inspections:
        status_frame = (
            pd.DataFrame(inspections)
            .groupby("status", as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )
        st.plotly_chart(
            px.bar(
                status_frame,
                x="status",
                y="count",
                color="status",
                title="Inspection Status",
            ),
            use_container_width=True,
        )


def render_vehicles() -> None:
    st.subheader("Vehicles")
    vehicles = load_vehicles()
    st.dataframe(dataframe_from_items(vehicles), use_container_width=True, hide_index=True)

    with st.expander("Create Vehicle"):
        with st.form("create_vehicle"):
            col1, col2, col3 = st.columns(3)
            vehicle_number = col1.text_input("Vehicle Number", value="MH12AB1234")
            make = col2.text_input("Make", value="Honda")
            model = col3.text_input("Model", value="City")
            year = col1.number_input("Year", min_value=1886, max_value=2100, value=2022)
            customer_name = col2.text_input("Customer Name", value="Test Customer")
            vin = col3.text_input("VIN", value="")
            submitted = st.form_submit_button("Create Vehicle")

        if submitted:
            payload = {
                "vehicle_number": vehicle_number,
                "make": make,
                "model": model,
                "year": int(year),
                "customer_name": customer_name,
                "vin": vin or None,
            }
            response = api_json("POST", "/api/vehicles", json=payload)
            if response:
                st.success("Vehicle created.")
                st.rerun()


def render_inspections() -> None:
    st.subheader("Inspections")
    inspections = load_inspections()
    st.dataframe(
        dataframe_from_items(inspections),
        use_container_width=True,
        hide_index=True,
    )

    vehicles = load_vehicles()
    vehicle_options = {f"{item['id']} - {item['vehicle_number']}": item["id"] for item in vehicles}

    with st.expander("Create Inspection"):
        if not vehicle_options:
            st.warning("Create a vehicle before creating an inspection.")
        else:
            with st.form("create_inspection"):
                selected_vehicle = st.selectbox("Vehicle", list(vehicle_options.keys()))
                overall_condition = st.selectbox(
                    "Overall Condition",
                    ["", "low", "medium", "high"],
                )
                submitted = st.form_submit_button("Create Inspection")
            if submitted:
                payload = {
                    "vehicle_id": vehicle_options[selected_vehicle],
                    "overall_condition": overall_condition or None,
                    "inspector_notes": None,
                }
                response = api_json("POST", "/api/inspections", json=payload)
                if response:
                    st.success("Inspection created.")
                    st.rerun()

    st.divider()
    if not inspections:
        st.info("No inspections found yet.")
        return

    inspection_options = {
        f"{item['id']} - vehicle {item['vehicle_id']} - {item['status']}": item["id"]
        for item in inspections
    }
    selected_inspection = st.selectbox(
        "Selected Inspection",
        list(inspection_options.keys()),
    )
    inspection_id = inspection_options[selected_inspection]
    selected = api_json("GET", f"/api/inspections/{inspection_id}")
    if not selected:
        return

    inspection = selected["data"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Status", inspection["status"])
    col2.metric("Vehicle ID", inspection["vehicle_id"])
    col3.metric("Inspector ID", inspection["inspector_id"])

    if inspection["status"] == "draft":
        uploaded = st.file_uploader("Upload Inspection Image", type=["jpg", "jpeg", "png"])
        image_view = st.selectbox(
            "Image View",
            ["front", "rear", "left", "right", "closeup_damage"],
        )
        if st.button("Upload Image", disabled=uploaded is None):
            if uploaded:
                files = {
                    "file": (
                        uploaded.name,
                        uploaded.getvalue(),
                        uploaded.type or "image/jpeg",
                    )
                }
                response = api_json(
                    "POST",
                    "/api/images/upload-one",
                    data={"inspection_id": str(inspection_id), "image_view": image_view},
                    files=files,
                )
                if response:
                    st.success("Image uploaded.")

    if inspection["status"] in {"draft", "ai_processing"}:
        if st.button("Run damage detection"):
            response = api_json(
                "POST",
                "/api/ai/analyze",
                json={"inspection_id": int(inspection_id)},
            )
            if response:
                st.success("AI analysis completed.")
                st.rerun()

    render_detection_review(
        int(inspection_id),
        inspection["status"],
        inspection.get("inspector_notes") or "",
    )

    if inspection["status"] == "under_review":
        complete_disabled = not (inspection.get("inspector_notes") or "").strip()
        if st.button("Complete Inspection", disabled=complete_disabled):
            response = api_json(
                "PUT",
                f"/api/inspections/{inspection_id}",
                json={"status": "completed"},
            )
            if response:
                st.success("Inspection completed.")
                st.rerun()
        if complete_disabled:
            st.warning("Inspection notes are required before completing this inspection.")


def render_detection_review(
    inspection_id: int,
    inspection_status: str,
    inspection_notes: str = "",
) -> None:
    response = api_json("GET", f"/api/ai/detections/{inspection_id}")
    if not response:
        return

    detections = response["data"]["items"]
    if not detections:
        st.info("No detections found for this inspection.")
        return

    st.subheader("Detections")
    st.dataframe(dataframe_from_items(detections), use_container_width=True, hide_index=True)

    if inspection_status != "under_review":
        return

    detection_options = {
        f"{item['id']} - {item['damage_type']} ({item['review_status']})": item
        for item in detections
    }
    selected_key = st.selectbox("Detection", list(detection_options.keys()))
    selected_detection = detection_options[selected_key]

    with st.form("review_detection"):
        status_value = st.selectbox("Review Status", ["approved", "rejected", "edited"])
        reviewed_damage_type = None
        reviewed_severity = None
        if status_value == "edited":
            reviewed_damage_type = st.selectbox(
                "Reviewed Damage Type",
                ["dent", "scratch", "broken_glass", "bumper_damage"],
                index=["dent", "scratch", "broken_glass", "bumper_damage"].index(
                    selected_detection["damage_type"]
                ),
            )
            reviewed_severity = st.selectbox(
                "Reviewed Severity",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(selected_detection["severity"]),
            )

        notes_value = st.text_area(
            "Inspection Notes",
            value=inspection_notes,
            help="Add inspection notes after AI analysis before completing this inspection.",
        )
        submitted = st.form_submit_button("Save Review")

    if submitted:
        payload: dict[str, Any] = {
            "review_status": status_value,
            "inspector_notes": selected_detection.get("inspector_notes") or None,
        }
        if status_value == "edited":
            payload["reviewed_damage_type"] = reviewed_damage_type
            payload["reviewed_severity"] = reviewed_severity

        if notes_value.strip():
            inspection_update = api_json(
                "PUT",
                f"/api/inspections/{inspection_id}",
                json={"inspector_notes": notes_value.strip()},
            )
            if inspection_update is None:
                return

        response = api_json(
            "PUT",
            f"/api/reviews/{selected_detection['id']}",
            json=payload,
        )
        if response:
            st.success("Review saved.")
            st.rerun()


def render_reports() -> None:
    st.subheader("Reports")
    reports = load_reports()
    st.dataframe(dataframe_from_items(reports), use_container_width=True, hide_index=True)

    inspections = load_inspections()
    if not inspections:
        st.info("No inspections found yet.")
        return

    inspection_options = {
        f"{item['id']} - vehicle {item['vehicle_id']} - {item['status']}": item["id"]
        for item in inspections
    }
    selected_inspection = st.selectbox(
        "Inspection",
        list(inspection_options.keys()),
        key="report_inspection",
    )
    inspection_id = inspection_options[selected_inspection]
    col1, col2, col3 = st.columns(3)
    if col1.button("Generate Report"):
        response = api_json(
            "POST",
            "/api/reports/generate",
            json={"inspection_id": int(inspection_id)},
        )
        if response:
            st.success("Report generated.")
            st.json(response["data"]["summary"])

    if col2.button("Load Report"):
        response = api_json("GET", f"/api/reports/{inspection_id}")
        if response:
            st.json(response["data"])

    if col3.button("Prepare Download"):
        pdf_bytes = api_file(f"/api/reports/{inspection_id}/download")
        if pdf_bytes:
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"inspection_{inspection_id}_report.pdf",
                mime="application/pdf",
            )


def main() -> None:
    _init_state()
    if not login_panel():
        return

    st.title("Vehicle Damage Inspection")
    tab_overview, tab_vehicles, tab_inspections, tab_reports = st.tabs(
        ["Overview", "Vehicles", "Inspections", "Reports"]
    )
    with tab_overview:
        render_overview()
    with tab_vehicles:
        render_vehicles()
    with tab_inspections:
        render_inspections()
    with tab_reports:
        render_reports()


if __name__ == "__main__":
    main()
