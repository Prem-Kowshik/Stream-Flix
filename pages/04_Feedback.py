
import streamlit as st
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="Feedback", layout="centered")

st.title("📋 App Review & Feedback")
st.write("We appreciate your time in reviewing our app. Please fill out the form below.")

# Embedded Google Form URL (transformed to iframe format)
form_url = "https://docs.google.com/forms/d/e/1FAIpQLSd-OSX-iNJIQiO36iHntoPpNIrPx4RcRkjh65i6QxENGnhj_A/viewform"

# Show the form inside an iframe
components.iframe(src=form_url, height=900, scrolling=True)

st.markdown("---")
st.subheader("✅ Confirm Submission")
st.write("Once you’ve submitted the form above, please click the button below to confirm.")

if st.button("I have submitted the feedback form"):
    st.success("Thank you for your feedback! 🎉 Redirecting you to the homepage...")

    # Simulate redirection or page switch
    time.sleep(2)
    # For multipage apps on Streamlit v1.22+, use: st.switch_page("Home.py")
    # For external redirect:
    st.switch_page("./Homepage.py")
