import streamlit as st
import pandas as pd
import numpy as np
import pickle
import os
from PIL import Image
import matplotlib.pyplot as plt

# --- Page Configuration (can be here or in individual pages) ---
st.set_page_config(layout="wide")

st.write("# 🛠️ Welcome to the Machinery Repair Operations Dashboard 👋")
st.markdown(
    """
This is your central hub for monitoring, analyzing, and optimizing equipment performance.
Use the sidebar to navigate through detailed insights, maintenance plans, and inventory analytics.
    """
)