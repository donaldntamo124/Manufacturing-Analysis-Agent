# Setup and Run Instructions

## Installation

### 1. Install Dependencies
```bash
cd "VSM GenAI"
pip install -r requirements.txt
```

This installs:
- **PySimpleGUI** (desktop GUI framework)
- **pandas** (data analysis)
- **openpyxl** (Excel file support)
- **LangChain** (AI agent orchestration)
- **LLM Provider SDKs** (OpenAI, Anthropic, Ollama)
- **fuzzywuzzy** (fuzzy column matching)

### 2. Configure Environment Variables

Copy the example to .env:
```bash
cp .env.example .env
```

Then edit `.env` with your API keys:
```env
# Choose your LLM provider:
LLM_PROVIDER=openai        # or anthropic, ollama

# If using OpenAI:
OPENAI_API_KEY=sk-...

# If using Anthropic:
ANTHROPIC_API_KEY=sk-ant-...

# If using Ollama (runs locally):
OLLAMA_MODEL=llama2        # or other local model
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Generate Test Data (Optional)
```bash
python tests/fixtures/generate_fixtures.py
```

This creates sample Excel files for testing:
- `simple_production.xlsx` - Clean data
- `messy_schedule.xlsx` - Non-standard column names
- `delayed_jobs.xlsx` - Overdue jobs
- `bottleneck_scenario.xlsx` - Process bottleneck

---

## Run the Application

```bash
python gui_app.py
```

A desktop window will open with the Manufacturing Analysis Agent.

### 3-Stage Workflow

**Stage 1: Upload & Preview**
1. Click "Browse" to select an Excel file
2. Select the sheet containing production data
3. Review the first 5 rows to verify data quality
4. Click "Next" to proceed

**Stage 2: Column Mapping**
1. Review the automatically detected column mappings
2. Confidence scores show match quality:
   - Green (85%+): Auto-mapped
   - Yellow (60-85%): Suggested (confirm or override)
   - Red (<60%): Requires manual mapping
3. Click column names to open mapping dialog if needed
4. Click "Confirm Mappings" to proceed

**Stage 3: Analysis & Results**
1. Type your question in natural language:
   - "What is the bottleneck in our production?"
   - "Which jobs are delayed?"
   - "What's the average cycle time?"
2. Click "Analyze" to run the query
3. Results appear in the output area
4. Click "Generate Report" to create an Excel file with detailed results

---

## Example Queries

- "What's the main bottleneck in our production process?"
- "Show me all delayed jobs"
- "How many jobs are in process for each machine?"
- "What's the average cycle time by process?"
- "Which machines have the highest utilization?"
- "Estimate our WIP levels"
- "Give me a summary of production efficiency"

---

## Generated Reports

When you click "Generate Report", you'll be prompted to save an Excel file containing:
- **Summary Statistics**: Total jobs, processing times, status breakdown
- **Bottleneck Analysis**: Process steps causing delays
- **Machine Utilization**: Job distribution by equipment
- **Process Efficiency**: Cycle times and throughput
- **Delayed Jobs**: List of overdue items with details
- **WIP Locations**: Work-in-process inventory estimates

---

## Troubleshooting

### "No module named PySimpleGUI"
```bash
pip install PySimpleGUI>=4.60.0
```

### "LangChain import error"
```bash
pip install --upgrade langchain langchain-core
```

### "API key not found"
1. Check that `.env` file exists in the project directory
2. Verify API keys are set correctly
3. Ensure the file format is correct (KEY=value)

### "Excel file won't load"
1. Verify the file is valid Excel (.xlsx format)
2. Check that it contains at least the required columns:
   - job_id
   - process_step
   - start_time
   - end_time

### GUI window doesn't appear
1. Ensure PySimpleGUI is installed: `pip install PySimpleGUI`
2. On Linux, you may need X11: `apt-get install xvfb`
3. Check that your display server is configured correctly

---

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Checking Code Quality
```bash
python -m py_compile gui_app.py src/*.py
```

### Generating New Test Data
Edit `tests/fixtures/generate_fixtures.py` to customize test datasets, then run:
```bash
python tests/fixtures/generate_fixtures.py
```

---

## File Structure

```
VSM GenAI/
├── gui_app.py                    # Main application (run this)
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
├── .env                          # Your configuration (git-ignored)
├── README.md                     # Documentation
├── src/
│   ├── agent.py                 # LangChain agent
│   ├── data_layer.py            # Excel I/O
│   ├── analysis_tools.py        # Analysis functions
│   └── config.py                # Constants & schema
└── tests/fixtures/
    └── generate_fixtures.py     # Test data generator
```

---

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Configure LLM**: Edit `.env` with your API key
3. **Generate test data**: `python tests/fixtures/generate_fixtures.py`
4. **Launch app**: `python gui_app.py`
5. **Load test file**: Select `simple_production.xlsx`
6. **Try a query**: "What is the bottleneck?"
7. **Generate report**: Click "Generate Report" to export results

---

## Support

For issues or questions:
1. Check that all dependencies are installed: `pip list | grep -i langchain`
2. Verify your `.env` file is correctly formatted
3. Test with a simple query first
4. Check the console output for error messages

---

**Ready to analyze manufacturing data!** 🚀
