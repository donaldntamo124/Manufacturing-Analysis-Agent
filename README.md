# Manufacturing Analysis Agent

A portfolio-ready GenAI agent application for analyzing manufacturing Excel files. Upload production data, ask natural language questions, and get AI-powered insights about bottlenecks, delays, and efficiency metrics.

## Features

- **Intelligent Excel Upload** - Automatically detects and maps column names using fuzzy matching
- **AI-Powered Analysis** - Natural language Q&A about your manufacturing data
- **Multi-Provider LLM Support** - Works with OpenAI, Anthropic (Claude), or local Ollama models
- **Manufacturing Insights** - Bottleneck detection, cycle time analysis, delayed job identification
- **Excel Report Generation** - Export detailed analysis results as professional Excel reports
- **Web UI** - Browser-based interface using Streamlit, works in Docker and dev containers

## Quick Start

### Prerequisites

- Python 3.11+
- Excel file with manufacturing data (see [Data Schema](#data-schema))

### Installation

1. **Clone or create the project:**
   ```bash
   cd /path/to/VSM\ GenAI
   ```

2. **Create a Python virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure LLM Provider:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

Opens in your browser at http://localhost:8501

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# LLM Provider (options: "openai", "anthropic", "ollama")
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo

# Anthropic Configuration
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Ollama Configuration (for local models)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Application Settings
DEBUG=false
MAX_FILE_SIZE_MB=100
```

### Supported LLM Providers

| Provider | Setup | Notes |
|----------|-------|-------|
| **OpenAI** | Set `OPENAI_API_KEY` | Recommended for quality |
| **Anthropic** | Set `ANTHROPIC_API_KEY` | Good for privacy |
| **Ollama** | Local setup required | Free, runs offline |

## Data Schema

### Required Columns

Your Excel file must contain at least these columns (names don't have to match exactly):

| Field | Type | Purpose |
|-------|------|---------|
| `job_id` | String | Unique job identifier |
| `process_step` | String | Manufacturing operation name |
| `start_time` | DateTime | When the job started |
| `end_time` | DateTime | When the job finished |

### Optional Columns

Additional columns will be automatically mapped if present:

| Field | Common Names | Type |
|-------|--------------|------|
| `machine` | Machine, Work Centre, Equipment | String |
| `operator` | Operator, Employee, Worker | String |
| `quantity` | Qty, Amount, Units | Number |
| `status` | Status, State, Progress | String |
| `due_date` | Due Date, Deadline | DateTime |
| `wip_location` | WIP Location, Current Location | String |

### Column Name Matching

The application uses fuzzy matching to automatically map your column names:

- Greater than or equal to 85% match: Automatically mapped
- 60-85% match: Suggested (you can confirm or override)
- Less than 60% match: Manual mapping required

## Example Queries

Try asking questions like:

- "What is the bottleneck in our production?"
- "Which jobs are delayed?"
- "What is the average cycle time?"
- "Which machines are underutilized?"
- "Where is work-in-progress concentrated?"
- "Give me a summary of today's production metrics"

## Application Architecture

### File Structure

```
VSM GenAI/
├── gui_app.py                  # Desktop GUI application
├── config.py                   # Schema definitions and constants
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── README.md                   # This file
├── src/
│   ├── data_layer.py          # Excel I/O and column mapping
│   ├── analysis_tools.py       # Manufacturing analysis functions
│   └── agent.py                # LangChain agent orchestration
└── tests/
    └── fixtures/               # Sample Excel files for testing
```

### Core Components

**data_layer.py**
- Reads Excel files and previews data
- Infers column mappings using fuzzy matching
- Cleans and standardizes data types

**analysis_tools.py**
- Calculates cycle times
- Identifies bottlenecks
- Finds delayed jobs
- Summarizes by machine and process
- Generates Excel reports

**agent.py**
- Routes to configured LLM provider
- Wraps analysis functions as tools
- Orchestrates multi-step reasoning

**gui_app.py**
- Desktop window interface
- 3-stage workflow: Upload/Preview -> Mapping -> Analysis
- File dialog integration
- Results display and report export

## Analysis Features

### Cycle Time Analysis
- Calculates end-to-end time for each job
- Identifies jobs with longest cycle times
- Ranks by process step

### Bottleneck Detection
- Finds process step with highest average cycle time
- Provides job count and total time metrics
- Actionable recommendations

### Delay Identification
- Compares end_time vs due_date
- Identifies status-flagged delays
- Lists delayed jobs with reasoning

### Machine and Process Summary
- Groups jobs by equipment
- Identifies underutilized resources
- Process-level rankings by cycle time

### WIP Location Analysis
- Detects where work-in-progress concentulates
- Identifies stalled or slow-moving jobs
- Provides inventory insights

## Usage Workflow

1. Run the application: `python gui_app.py`
2. Upload your Excel file and select a sheet
3. Review data preview and confirm column mappings
4. Ask questions about your manufacturing data
5. View results and generate Excel reports

## Technical Details

### Dependencies

- **PySimpleGUI** - Desktop GUI framework
- **pandas** - Data manipulation and analysis
- **openpyxl** - Excel file I/O
- **LangChain** - LLM orchestration and tool calling
- **fuzzywuzzy** - Fuzzy string matching for column inference
- **python-dotenv** - Environment configuration

### LLM Integration

The agent uses tool-calling (function calling) to invoke analysis functions:

1. User asks a natural language question
2. LLM determines which analysis tools are needed
3. Tools execute and return results
4. LLM synthesizes results into a natural language response

### Error Handling

The application gracefully handles:
- Missing or malformed Excel files
- Invalid date formats
- Missing required columns
- LLM API timeouts
- Memory limits for large datasets

## 🎓 Lessons Learned & Design Decisions

### Why Separate LLM from Calculations?

Manufacturing analysis requires **reproducibility** and **auditability**. By using Python for deterministic calculations and LLM only for reasoning:
- Results are debuggable and verifiable
- No hallucination in numeric outputs
- Calculations are deterministic across runs

### Why Fuzzy Matching for Columns?

Manufacturing data is messy:
- Different facilities use different column names
- Users may use abbreviations or local terminology
- Fuzzy matching handles spelling variations

### Why PySimpleGUI for Desktop?

For a traditional desktop application:
- Simple, intuitive interface for data analysis tasks
- No web browser required
- Cross-platform (Windows, Mac, Linux)
- Lightweight and fast
- Easy to package and distribute

### Why LangChain + Simple Tools (Not LangGraph)?

For MVP scope:
- LangChain's tool-calling is sufficient for single-turn reasoning
- Simpler to debug and maintain
- Easier learning curve for portfolio reviewers
- LangGraph is reserved for future multi-step workflows

## Known Limitations

- File Size: Tested with files up to 100MB; very large datasets (over 1 million rows) may be slow
- Timezone Handling: All timestamps converted to UTC; timezone info from Excel is discarded
- Column Matching: Very unusual column names (less than 60% fuzzy match) require manual mapping
- Date Formats: Supports common formats; exotic formats may need pre-processing
- LLM Quality: Analysis quality depends on LLM provider; GPT-4 or Claude-3 recommended

## Future Enhancements

- Multi-file analysis - Compare production across multiple Excel files
- Time-series forecasting - Predict future delays based on historical data
- Custom metrics - User-defined KPI calculations
- Database backend - Store and version analysis results
- Advanced scheduling - Integration with production planning systems
- Predictive maintenance - Equipment failure prediction
- Real-time dashboards - Live production monitoring

## Example: Creating Test Data

```python
import pandas as pd
from datetime import datetime, timedelta

# Create sample manufacturing data
data = {
    "Job ID": ["J001", "J002", "J003"],
    "Operation": ["Assembly", "Testing", "Assembly"],
    "Start Time": [
        datetime(2024, 1, 1, 8, 0),
        datetime(2024, 1, 1, 10, 30),
        datetime(2024, 1, 1, 14, 0),
    ],
    "Finish Time": [
        datetime(2024, 1, 1, 10, 15),
        datetime(2024, 1, 1, 12, 45),
        datetime(2024, 1, 1, 16, 30),
    ],
}

df = pd.DataFrame(data)
df.to_excel("sample_production.xlsx", index=False)
```

## Contributing

To extend this project:

1. Add new analysis functions to `src/analysis_tools.py`
2. Wrap them as LangChain tools in `src/agent.py`
3. Test with `tests/fixtures/` sample data
4. Update README with new capabilities

## License

This is a portfolio project. Feel free to use as reference or starting point.

## Support

For issues or questions:
- Check the `.env.example` for configuration
- Review console output for error messages
- Verify Excel file has required columns
- Test with `tests/fixtures/` sample files
- Check LLM provider API keys and quotas

## Testing

Generate test fixtures:
```bash
python tests/fixtures/generate_fixtures.py
```

This creates sample Excel files in `tests/fixtures/`:
- `simple_production.xlsx` - Clean data with standard names
- `messy_schedule.xlsx` - Non-standard column names
- `delayed_jobs.xlsx` - Contains overdue jobs
- `bottleneck_scenario.xlsx` - Shows bottleneck process

Then load these files in the GUI application to test functionality.

---

Built for manufacturing professionals who need data-driven insights.
