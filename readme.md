# Column Mapping Advisor

An AI-powered column mapping tool that intelligently maps your dataset columns to standardized column names, with interactive mapping capabilities and category-based standardization.

## 🌟 Features

- **Intelligent Category Detection**: Automatically identifies dataset category (billing, usage, support)
- **Smart Column Mapping**: Generates contextual column mapping suggestions
- **Interactive Mapping**: Review and modify AI-suggested mappings
- **Flexible Data Input**: Supports multiple file formats (CSV, Excel, JSON, Parquet)
- **Visual Progress Tracking**: Clear feedback on mapping progress
- **Data Export**: Download mapped data in CSV format

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:

```bash
git clone https://github.com/stepfnAI/mapping_agent.git
cd mapping_agent
```

2. Create and activate a virtual environment using virtualenv:

```bash
pip install virtualenv                # Install virtualenv if not already installed
virtualenv venv                       # Create virtual environment
source venv/bin/activate             # Linux/Mac
# OR
.\venv\Scripts\activate              # Windows
```

3. Install the package in editable mode:

```bash
pip install -e .
```

4. Set up your OpenAI API key:

```bash
export OPENAI_API_KEY='your_openai_api_key'
```

### Running the Application

```bash
streamlit run .\examples\app.py
```

## 🔄 Workflow

1. **Data Loading and Preview**
   - Upload your dataset (CSV, Excel, JSON, or Parquet)
   - Preview the loaded data
   - Reset functionality available at any point

2. **Category Identification**
   - AI automatically analyzes and suggests dataset category
   - Options to:
     - Confirm AI suggestion
     - Select different category (Billing, Usage, Support)

3. **Column Mapping**
   - AI suggests mappings based on standard columns
   - Interactive review and modification with:
     - Visual indicators for mandatory columns (\#)
     - Dropdown selection for each column mapping
     - Option to map additional standard columns
     - Validation for mandatory column mappings
   - Mapping confirmation only possible after all mandatory columns are mapped

4. **Post Processing**
   - Three operation options:
     - View mapped data
     - Download processed dataset (CSV format)
     - Finish and reset application

## 🛠️ Architecture

The application follows a modular architecture with these key components:

- **SFNCategoryIdentificationAgent**: Identifies dataset category
- **SFNColumnMappingAgent**: Generates column mapping suggestions
- **SFNDataLoader**: Handles data import
- **SFNDataPostProcessor**: Manages data export
- **StreamlitView**: Manages user interface
- **SFNSessionManager**: Handles application state

## 🔒 Security

- Secure API key handling
- Input validation
- Safe data processing
- Environment variable management

## 📊 Mapping Features

The tool supports mapping for various data categories:

### Billing Columns
- Revenue metrics
- Customer information
- Contract details
- Product information
- Pricing data

### Usage Columns
- License metrics
- Feature usage
- Activity tracking
- User engagement

### Support Columns
- Ticket information
- Response metrics
- Customer satisfaction
- Case management

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

Email: puneet@stepfunction.ai