"""
Manufacturing Analysis Agent - GUI Application
Traditional desktop application using PySimpleGUI
"""

import PySimpleGUI as sg
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import threading

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

# Load environment variables
load_dotenv()

# Set PySimpleGUI theme
sg.theme('DarkBlue3')

# Application state
app_state = {
    'file_path': None,
    'sheet_name': None,
    'df': None,
    'mapping': None,
    'mapping_confirmed': False,
    'excel_metadata': None,
    'analysis_results': None,
}


def show_file_upload_window():
    """Initial window for file upload and sheet selection."""
    layout = [
        [sg.Text('Manufacturing Analysis Agent', font=('Arial', 16, 'bold'))],
        [sg.Text('Upload an Excel file with manufacturing data', font=('Arial', 10))],
        [sg.Text('')],
        
        [sg.Text('Select Excel File:', font=('Arial', 10, 'bold'))],
        [sg.Input(key='-FILE-', readonly=True, size=(50, 1)), 
         sg.FileBrowse(file_types=(('Excel Files', '*.xlsx *.xls'),))],
        [sg.Text('')],
        
        [sg.Listbox([], size=(60, 8), key='-SHEETS-', 
                   select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
        [sg.Text('Available sheets will appear above', font=('Arial', 9), text_color='gray')],
        [sg.Text('')],
        
        [sg.Button('Load Sheet', size=(12, 1)), 
         sg.Button('Exit', size=(12, 1))],
    ]
    
    window = sg.Window('Manufacturing Analysis Agent', layout)
    
    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            window.close()
            return None
        
        if event == '-FILE-' or values['-FILE-'] != app_state.get('file_path'):
            file_path = values['-FILE-']
            if file_path and Path(file_path).exists():
                try:
                    metadata = read_excel_file(file_path)
                    app_state['file_path'] = file_path
                    app_state['excel_metadata'] = metadata
                    window['-SHEETS-'].update(metadata['sheets'])
                except Exception as e:
                    sg.popup_error(f'Error reading file: {str(e)}')
                    window['-SHEETS-'].update([])
        
        if event == 'Load Sheet':
            sheets = values['-SHEETS-']
            if not sheets:
                sg.popup_error('Please select a sheet')
                continue
            
            app_state['sheet_name'] = sheets[0]
            window.close()
            return app_state['file_path']
    
    window.close()
    return None


def show_preview_and_mapping_window(file_path, sheet_name):
    """Window for data preview and column mapping."""
    try:
        # Load data
        preview_df = preview_sheet(file_path, sheet_name, rows=5)
        full_df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Infer mapping
        inferred_mapping = infer_column_mapping(full_df.columns.tolist())
        
        # Validate required columns
        is_valid, missing = validate_required_columns(inferred_mapping)
        
        if not is_valid:
            sg.popup_error(f'Missing required columns: {", ".join(missing)}\n\n'
                          f'Required: {", ".join(REQUIRED_COLUMNS)}')
            return False
        
        # Build display table
        mapping_display = []
        for schema_field, (user_column, confidence) in inferred_mapping.items():
            conf_pct = int(confidence)
            if conf_pct >= FUZZY_MATCH_THRESHOLDS['auto_map']:
                status = 'Auto-mapped'
            elif conf_pct >= FUZZY_MATCH_THRESHOLDS['suggest']:
                status = 'Suggested'
            else:
                status = 'Manual'
            mapping_display.append([schema_field, user_column, f'{conf_pct}%', status])
        
        # Preview table
        preview_display = []
        for idx, row in preview_df.iterrows():
            preview_display.append(list(row.values))
        
        layout = [
            [sg.Text('Data Preview and Column Mapping', font=('Arial', 14, 'bold'))],
            [sg.Text(f'File: {Path(file_path).name} | Sheet: {sheet_name}')],
            [sg.Text('')],
            
            [sg.Text('First 5 rows:', font=('Arial', 10, 'bold'))],
            [sg.Table(values=preview_display, 
                     headings=preview_df.columns.tolist(),
                     size=(80, 6),
                     key='-PREVIEW-')],
            [sg.Text('')],
            
            [sg.Text('Column Mapping (Auto-detected):', font=('Arial', 10, 'bold'))],
            [sg.Table(values=mapping_display,
                     headings=['Schema Field', 'User Column', 'Confidence', 'Status'],
                     size=(80, 10),
                     key='-MAPPING-')],
            [sg.Text(f'Total records: {len(full_df)}', font=('Arial', 9))],
            [sg.Text('')],
            
            [sg.Checkbox('I confirm this mapping', key='-CONFIRM-', default=False)],
            [sg.Button('Proceed', size=(12, 1), disabled=True, key='-PROCEED-'),
             sg.Button('Back', size=(12, 1))],
        ]
        
        window = sg.Window('Preview and Mapping', layout)
        
        while True:
            event, values = window.read()
            
            if event == sg.WINDOW_CLOSED or event == 'Back':
                window.close()
                return False
            
            if event == '-CONFIRM-':
                window['-PROCEED-'].update(disabled=not values['-CONFIRM-'])
            
            if event == '-PROCEED-':
                # Apply mapping and clean data
                try:
                    cleaned_df = clean_and_standardize_data(full_df, inferred_mapping)
                    app_state['df'] = cleaned_df
                    app_state['mapping'] = inferred_mapping
                    app_state['mapping_confirmed'] = True
                    window.close()
                    return True
                except Exception as e:
                    sg.popup_error(f'Error standardizing data: {str(e)}')
        
        window.close()
        return False
    
    except Exception as e:
        sg.popup_error(f'Error: {str(e)}')
        return False


def show_analysis_window():
    """Window for querying and analyzing the data."""
    layout = [
        [sg.Text('Analysis and Query', font=('Arial', 14, 'bold'))],
        [sg.Text(f'Records: {len(app_state["df"])} | Columns: {len(app_state["df"].columns)}')],
        [sg.Text('')],
        
        [sg.Text('Ask a question about your manufacturing data:', font=('Arial', 10, 'bold'))],
        [sg.Multiline(size=(80, 3), key='-QUERY-', 
                     default_text='What is the bottleneck in our production?')],
        [sg.Text('')],
        
        [sg.Button('Analyze', size=(12, 1)), 
         sg.Button('Generate Report', size=(15, 1)),
         sg.Button('Done', size=(12, 1))],
        [sg.Text('')],
        
        [sg.Multiline(size=(80, 15), key='-RESULTS-', disabled=True, 
                     default_text='Results will appear here...')],
    ]
    
    window = sg.Window('Analysis', layout, finalize=True)
    
    while True:
        event, values = window.read(timeout=100)
        
        if event == sg.WINDOW_CLOSED or event == 'Done':
            window.close()
            break
        
        if event == 'Analyze':
            query = values['-QUERY-'].strip()
            if not query:
                sg.popup_error('Please enter a question')
                continue
            
            # Run analysis in a thread to keep UI responsive
            window['-RESULTS-'].update('Analyzing... please wait...')
            window.refresh()
            
            try:
                results = run_agent(
                    user_query=query,
                    file_path=app_state['file_path'],
                    sheet_name=app_state['sheet_name'],
                    mapping=app_state['mapping'],
                    df=app_state['df'],
                )
                
                app_state['analysis_results'] = results
                
                # Format output
                output = 'ANALYSIS RESULTS\n'
                output += '=' * 80 + '\n\n'
                output += 'Answer:\n'
                output += results.get('final_answer', 'No response') + '\n\n'
                
                if results.get('summary_statistics'):
                    output += '\nSummary Statistics:\n'
                    output += '-' * 40 + '\n'
                    stats = results['summary_statistics']
                    for key, value in stats.items():
                        output += f'{key}: {value}\n'
                
                if results.get('bottleneck_analysis'):
                    output += '\nBottleneck Analysis:\n'
                    output += '-' * 40 + '\n'
                    bn = results['bottleneck_analysis']
                    output += f'Bottleneck: {bn["bottleneck_process"]}\n'
                    output += f'Avg Cycle Time: {bn["avg_cycle_time"]} minutes\n'
                    output += f'Job Count: {bn["job_count"]}\n'
                
                window['-RESULTS-'].update(output)
            
            except Exception as e:
                window['-RESULTS-'].update(f'Error: {str(e)}')
        
        if event == 'Generate Report':
            if not app_state['analysis_results']:
                sg.popup_error('Please run an analysis first')
                continue
            
            try:
                file_path = sg.popup_get_file(
                    'Save report as:',
                    save_as=True,
                    file_types=(('Excel Files', '*.xlsx'),),
                    default_extension='.xlsx'
                )
                
                if file_path:
                    report_path = generate_excel_report(
                        results=app_state['analysis_results'],
                        output_path=file_path,
                        df=app_state['df'],
                    )
                    sg.popup(f'Report saved to:\n{report_path}')
            
            except Exception as e:
                sg.popup_error(f'Error generating report: {str(e)}')


def main():
    """Main application flow."""
    # Step 1: File upload
    file_path = show_file_upload_window()
    if not file_path:
        return
    
    # Step 2: Preview and mapping
    if not show_preview_and_mapping_window(file_path, app_state['sheet_name']):
        sg.popup_error('Failed to load data. Exiting.')
        return
    
    # Step 3: Analysis
    sg.popup(f'Data loaded successfully!\n'
            f'Records: {len(app_state["df"])}\n'
            f'Columns: {len(app_state["df"].columns)}')
    show_analysis_window()
    
    sg.popup('Thank you for using Manufacturing Analysis Agent')


if __name__ == '__main__':
    main()
