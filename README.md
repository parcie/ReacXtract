## ReacXtract
ReacXtract is a multimodal LLM-based System for Automated Chemical Reaction Extraction from Scientific Documents
ReacXtract is a research-oriented software framework for extracting structured chemical reaction information from heterogeneous scientific documents. It integrates rule-based preprocessing with large language models (LLMs) to convert unstructured chemical literature into standardized, machine-readable reaction representations.

The system supports multiple document formats and is distributed as a **desktop application with a native Windows installer (Electron-based)**, enabling one-click deployment and execution

## Key Features
- **Multimodal document support**
	PDF / XML / TXT / ChemDraw CDX

- **LLM-assisted reaction extraction**
	Semantic parsing using GPT-style models

- **Unified structured output**
	Standardized JSON reaction schema

- **End-to-end system integration**
	Backend + API + desktop GUI fully connected

- **One-click desktop deployment**
	Windows installer (.exe) based on Electron packaging
	No manual environment setup required

- **Automatic backend orchestration**
	Python FastAPI service is launched and managed by the desktop application
## Project Architecture
```text
ReacXtract
├── core.py                  # Core pipeline
├── main.js                  # Electron desktop launcher
├── pipeline/
│   ├── XML_full_process.py  # XML pipeline
│   ├── TXT_full_process.py  # TXT pipeline
│   └── PDF_full_process.py  # PDF pipeline
└── tools/
    ├── CDX_reading/
    ├── PDF_reading/
    ├── XML_reading/
    ├── TXT_reading/
    └── AI_interaction/
```
## System workflow
	Scientific Documents
	(PDF / XML / TXT / CDX)
	        │
	        ▼
	Format-specific Parsing Layer
	        │
	        ▼
	Intermediate Structured Text
	        │
	        ▼
	LLM-based Reaction Extraction
	        │
	        ▼
	Normalization Layer
	        │
	        ▼
	Structured JSON Output
	        │
	        ▼
	Desktop / API Interface
	(Electron App + FastAPI Backend)
  
## Installation
### 1. desktop application
   
- **`ReacXtract.exe`** — for direct running (backend only)
- **`ReacXtract Setup 1.0.0.exe`** — for complete desktop application installation package (including the interface)
> The application waits for the FastAPI service to be available (`127.0.0.1:8000`)
For developers to o run backend manually and launch desktop app under dev mode
```bash
# Start backend
uvicorn app:app --host 127.0.0.1 --port 8000

# Start frontend (in electron folder)
npm install
npm start
```

### 2. package installation & using
Clone repository
```bash
# clone repository
git clone https://github.com/yourname/ReacXtract.git
cd ReacXtract
# create environment
conda create -n reacxtract python=3.10
conda activate reacxtract
# instal dependencies
pip install -r requirements.txt
```

API key setup
```bash
export OPENAI_API_KEY="your_api_key"
```

for python usage
```python
from core import whole_pipeline
results = whole_pipeline(
api_key="YOUR_API_KEY",
file_list=["paper.pdf", "patent.xml"],
output_file="reactions.json"
)
```

## Proprietary Components
The CDX parsing and reaction extraction functionality in this project is based on collaborative development with an industrial partner.

The public release of ReacXtract includes a simplified CDX processing module intended for testing, demonstration, and research reproducibility. Some advanced features from the internal research version are not included or have been simplified.

Nevertheless, the overall architecture and API interfaces remain fully compatible with future extensions and alternative CDX processing backends.

This design maintains the reproducibility and extensibility of ReacXtract while respecting collaborative development and intellectual property considerations.

