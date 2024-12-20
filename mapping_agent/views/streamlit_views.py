from sfn_blueprint.views.streamlit_view import SFNStreamlitView
from typing import List, Optional
import streamlit as st

class StreamlitView(SFNStreamlitView):
    
    def select_box(self, label: str, options: List[str], key: Optional[str] = None) -> str:
        return st.selectbox(label, options, key=key)

    def display_button(self, label: str, key: Optional[str] = None, use_container_width: bool = False) -> bool:
        """Display a button with proper labeling"""
        button_key = key if key else f"button_{label}"
        return st.button(label=label, key=button_key, use_container_width=use_container_width)
        
    def file_uploader(self, label: str, key: str, accepted_types: List[str]) -> Optional[str]:
        return st.file_uploader(label, key=key, type=accepted_types)