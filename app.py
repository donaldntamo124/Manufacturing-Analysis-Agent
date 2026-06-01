"""
Streamlit web application for Manufacturing Analysis Agent.
Provides a user-friendly interface for uploading Excel files and analyzing manufacturing data.
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import application modules
from src.data_layer import (
    read_excel_file,
    preview_sheet,
    infer_column_mapping,
    validate_required_columns,
    clean_and_standardize_data,
)
from src.analysis_tools import generate_excel_report
from src.agent import run_agent
from src.config import REQUIRED_COLUMNS, FUZZY_MATCH_THRESHOLDS


# ============================================================================
# Streamlit Configuration
# ============================================================================

st.set_page_config(
    page_title="Manufacturing Analysis Agent",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏭 Manufacturing Analysis Agent")
st.markdown(
    """
    Upload an Excel file with manufacturing data and ask questions about your production.
    The agent will analyze your data and provide insights about bottlenecks, delays, and efficiency.
    """
)


# ============================================================================
# Session State Initialization
# ============================================================================

def initialize_session_state():
    """Initialize all required session state variables."""
    if "file_path" not in st.session_state:
        st.session_state.file_path = None
    if "sheet_name" not in st.session_state:
        st.session_state.sheet_name = None
    if "df" not in st.session_state:
        st.session_state.df = None
    if "mapping" not in st.session_state:
        st.session_state.mapping = None
    if "mapping_confirmed" not in st.session_state:
        st.session_state.mapping_confirmed = False
    if "excel_file_metadata" not in st.session_state:
        st.session_state.excel_file_metadata = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None


initialize_session_state()


# ============================================================================
# Section 1: File Upload
# ============================================================================

st.header("📁 Step 1: Upload Excel File")

uploaded_file = st.file_uploader(
    "Choose an Excel file with manufacturing data",
    type=["xlsx", "xls"],
    help="Supported formats: .xlsx (recommended), .xls"
)

if uploaded_file:
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        temp_path = tmp_file.name
    
    st.session_state.file_path = temp_path
    
    # Read file metadata
    try:
        metadata = read_excel_file(temp_path)
        st.session_state.excel_file_metadata = metadata
        
        st.success(f"✅ File uploaded: {metadata['file_name']}")
        st.info(f"Available sheets: {', '.join(metadata['sheets'])}")
        
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.stop()


# ============================================================================
# Section 2: Sheet Selection & Preview
# ============================================================================

if st.session_state.file_path:
    st.header("🔍 Step 2: Select Sheet & Preview Data")
    
    sheet_options = st.session_state.excel_file_metadata["sheets"]
    selected_sheet = st.selectbox(
        "Choose a sheet to analyze",
        sheet_options,
        index=0,
        key="sheet_selector",
    )
    
    st.session_state.sheet_name = selected_sheet
    
    # Preview data
    try:
        preview_df = preview_sheet(st.session_state.file_path, selected_sheet, rows=5)
        
        st.subheader("Data Preview (First 5 rows)")
        st.dataframe(preview_df, use_container_width=True)
        
        st.info(f"📊 Sheet contains {len(preview_df)} rows visible in preview")
        st.markdown(f"**Columns found:** {', '.join(preview_df.columns.tolist())}")
        
    except Exception as e:
        st.error(f"❌ Error previewing sheet: {str(e)}")
        st.stop()


# ============================================================================
# Section 3: Column Mapping
# ============================================================================

if st.session_state.sheet_name and not st.session_state.mapping_confirmed:
    st.header("🔗 Step 3: Map Columns to Standard Schema")
    
    # Load full data for mapping
    try:
        full_df = pd.read_excel(st.session_state.file_path, sheet_name=st.session_state.sheet_name)
        
        # Auto-infer mapping
        st.subheader("Auto-detected Column Mapping")
        st.info("The system uses fuzzy matching to suggest mappings. Review and confirm below.")
        
        inferred_mapping = infer_column_mapping(full_df.columns.tolist())
        
        # Display confidence scores
        mapping_data = []
        for schema_field, (user_column, confidence) in inferred_mapping.items():
            confidence_pct = int(confidence)
            if confidence_pct >= FUZZY_MATCH_THRESHOLDS["auto_map"]:
                status = "✅ Auto-mapped"
            elif confidence_pct >= FUZZY_MATCH_THRESHOLDS["suggest"]:
                status = "⚠️ Suggested"
            else:
                status = "❓ Manual"
            
            mapping_data.append({
                "Schema Field": schema_field,
                "User Column": user_column,
                "Confidence": f"{confidence_pct}%",
                "Status": status,
            })
        
        mapping_table = pd.DataFrame(mapping_data)
        st.dataframe(mapping_table, use_container_width=True)
        
        # Validate required columns
        is_valid, missing = validate_required_columns(inferred_mapping)
        
        if not is_valid:
            st.error(f"❌ Missing required columns: {', '.join(missing)}")
            st.info("Please ensure your data contains the following columns:")
            for req_col in REQUIRED_COLUMNS:
                st.write(f"  - {req_col}")
            st.stop()
        
        else:
            st.success(f"✅ All required columns found: {', '.join(REQUIRED_COLUMNS)}")
        
        # Manual adjustment section
        with st.expander("🔧 Advanced: Manually Edit Mappings"):
            st.write("You can override the auto-detected mappings here:")
            
            manual_mapping = {}
            for schema_field in inferred_mapping.keys():
                selected_col = st.selectbox(
                    f"Select column for '{schema_field}'",
                    options=[None] + full_df.columns.tolist(),
                    index=None,
                    key=f"manual_{schema_field}",
                )
                if selected_col:
                    manual_mapping[schema_field] = (selected_col, 100)
            
            if manual_mapping:
                inferred_mapping.update(manual_mapping)
        
        # Confirm mapping button
        if st.button("✅ Confirm Column Mapping & Load Data", key="confirm_mapping"):
            try:
                # Clean and standardize data
                cleaned_df = clean_and_standardize_data(full_df, inferred_mapping)
                
                st.session_state.df = cleaned_df
                st.session_state.mapping = inferred_mapping
                st.session_state.mapping_confirmed = True
                
                st.success(f"✅ Data standardized! Loaded {len(cleaned_df)} records with {len(cleaned_df.columns)} columns.")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error standardizing data: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.stop()


# ============================================================================
# Section 4: Analysis & Query
# ============================================================================

if st.session_state.mapping_confirmed and st.session_state.df is not None:
    st.header("💬 Step 4: Ask Questions About Your Data")
    
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        user_query = st.text_input(
            "What would you like to know about your manufacturing data?",
            placeholder="E.g., 'What is the bottleneck in our production?', 'Which jobs are delayed?'",
            key="query_input",
        )
    
    with col2:
        analyze_button = st.button("🔍 Analyze", key="analyze_btn", use_container_width=True)
    
    # Example queries
    with st.expander("💡 Example Questions"):
        examples = [
            "What is the bottleneck in our production process?",
            "Which jobs are currently delayed?",
            "Which machines are underutilized?",
            "What is the average cycle time by process step?",
            "Where is work-in-progress concentrated?",
            "What are the key metrics for today's production?",
        ]
        for example in examples:
            st.write(f"• {example}")
    
    # Process query
    if analyze_button and user_query:
        with st.spinner("🤖 Analyzing data..."):
            try:
                results = run_agent(
                    user_query=user_query,
                    file_path=st.session_state.file_path,
                    sheet_name=st.session_state.sheet_name,
                    mapping=st.session_state.mapping,
                    df=st.session_state.df,
                )
                
                st.session_state.analysis_results = results
                
                # Display results
                st.subheader("📊 Analysis Results")
                
                if results.get("status") == "error":
                    st.error(f"❌ Analysis error: {results.get('error_message')}")
                else:
                    # Main answer
                    st.write(results.get("final_answer", "No response"))
                    
                    # Display summary statistics
                    if results.get("summary_statistics"):
                        st.subheader("📈 Summary Statistics")
                        stats = results["summary_statistics"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Jobs", stats.get("total_jobs", "N/A"))
                        with col2:
                            st.metric("Avg Cycle Time (min)", f"{stats.get('avg_cycle_time', 0):.1f}")
                        with col3:
                            st.metric("Min Cycle Time (min)", f"{stats.get('min_cycle_time', 0):.1f}")
                        with col4:
                            st.metric("Max Cycle Time (min)", f"{stats.get('max_cycle_time', 0):.1f}")
                    
                    # Display bottleneck info
                    if results.get("bottleneck_analysis"):
                        st.subheader("🚫 Bottleneck Analysis")
                        bottleneck = results["bottleneck_analysis"]
                        st.info(
                            f"**{bottleneck['bottleneck_process']}** is the bottleneck\n\n"
                            f"Average cycle time: {bottleneck['avg_cycle_time']} minutes\n"
                            f"Total jobs processed: {bottleneck['job_count']}"
                        )
                    
                    # Debug section
                    with st.expander("🔬 Debug Information"):
                        st.json(results)
            
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")


# ============================================================================
# Section 5: Report Download
# ============================================================================

if st.session_state.mapping_confirmed and st.session_state.df is not None:
    st.header("📥 Step 5: Download Report")
    
    if st.button("📊 Generate Excel Report", key="gen_report_btn"):
        with st.spinner("Generating report..."):
            try:
                # Use existing analysis results or generate fresh ones
                results = st.session_state.analysis_results or {
                    "summary_statistics": None,
                    "bottleneck_analysis": None,
                }
                
                # Generate report
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_report:
                    report_path = tmp_report.name
                
                report_path = generate_excel_report(
                    results=results,
                    output_path=report_path,
                    df=st.session_state.df,
                )
                
                # Read report for download
                with open(report_path, "rb") as f:
                    report_data = f.read()
                
                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=report_data,
                    file_name="manufacturing_analysis_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                
                st.success("✅ Report generated successfully!")
                
                # Clean up temp file
                os.unlink(report_path)
            
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")


# ============================================================================
# Sidebar: Information & Reset
# ============================================================================

with st.sidebar:
    st.title("ℹ️ Information")
    
    st.markdown("""
    ### About This Tool
    This Manufacturing Analysis Agent helps you understand your production data by:
    
    - **Mapping** your Excel columns to a standard schema
    - **Analyzing** cycle times, bottlenecks, and delays
    - **Generating** actionable insights via AI
    - **Exporting** detailed reports
    
    ### Supported Data
    - Excel files (.xlsx, .xls)
    - Manufacturing production data
    - Job tracking information
    
    ### Key Features
    - ✅ Automatic column mapping with fuzzy matching
    - 🤖 AI-powered analysis using LangChain
    - 📊 Multi-provider LLM support
    - 📥 Excel report generation
    """)
    
    st.divider()
    
    if st.session_state.mapping_confirmed:
        st.markdown("### Current Session")
        st.write(f"**File:** {st.session_state.excel_file_metadata.get('file_name', 'Unknown')}")
        st.write(f"**Sheet:** {st.session_state.sheet_name}")
        st.write(f"**Records:** {len(st.session_state.df)}")
        st.write(f"**Columns:** {len(st.session_state.df.columns)}")
    
    st.divider()
    
    if st.button("🔄 Reset Session", key="reset_btn"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.divider()
    
    st.markdown("""
    ### Configuration
    Make sure to set up your `.env` file with:
    - `LLM_PROVIDER` (openai, anthropic, or ollama)
    - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
    - `OLLAMA_BASE_URL` (if using Ollama)
    """)


# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown(
    """
    <div style="text-align: center; color: gray; font-size: 0.8rem; margin-top: 2rem;">
    Manufacturing Analysis Agent • Powered by LangChain & Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
