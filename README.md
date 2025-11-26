# Evaluating the Quality of User Stories: An Extended Comparative Study of Multiple LLMs and Rule-Based Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-412991.svg)](https://openai.com/)

> **Supplementary Material for Research Paper**  
> Extended comparative study of GPT-5, GPT-5-mini, and GPT-4 for automated user story quality evaluation using the Quality User Story (QUS) Framework

## 📋 Table of Contents

- [Overview](#overview)
- [Research Questions](#research-questions)
- [Methodology](#methodology)
- [Repository Structure](#repository-structure)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [Data Description](#data-description)
- [Results](#results)
- [Citation](#citation)
- [License](#license)
- [Authors](#authors)

## 🎯 Overview

This repository contains the supplementary materials, code, and data for our research on **automated user story quality evaluation using Large Language Models (LLMs)**. We investigate how GPT models can identify quality defects in agile user stories based on the **Quality User Story (QUS) Framework**.

### Key Contributions

- **Extended Comparative Study**: Comprehensive evaluation of GPT-5, GPT-5-mini, and GPT-4
- **Automated Quality Analysis**: Leveraging LLMs to detect syntactic and pragmatic defects in user stories
- **QUS Framework Implementation**: Systematic evaluation across 7 quality criteria
- **Multi-Model Comparison**: Performance analysis across three GPT model generations
- **Real-World Datasets**: Analysis of user stories from 3 open-source projects

### QUS Framework Criteria

The Quality User Story (QUS) Framework evaluates user stories across two dimensions:

**Syntactic Quality (Textual Structure)**

1. `well_formed.no_role` - Missing role definition
2. `well_formed.no_means` - Missing desired action
3. `atomic.conjunctions` - Multiple features in one story
4. `minimal.punctuation` - Excessive supplemental notes
5. `minimal.brackets` - Unnecessary bracketed content

**Pragmatic Quality (Agile Practice Compliance)** 6. `unique.identical` - Duplicate stories 7. `uniform.uniform` - Inconsistent phrasing patterns

## 🔬 Research Questions

**RQ1**: How accurately can LLMs identify quality defects in user stories according to the QUS Framework?

**RQ2**: What types of defects (syntactic vs. pragmatic) are LLMs better at detecting?

**RQ3**: How do different GPT model versions compare in user story quality evaluation?

## 🔧 Methodology

### Experimental Design

1. **Dataset Selection**: 3 open-source projects with real user stories

   - g13-planningpoker (53 stories)
   - g21-badcamp (68 stories)
   - g28-zooniverse (47 stories)

2. **Model Selection**: OpenAI GPT models

   - GPT-4 (baseline)
   - GPT-5-mini (efficiency)
   - GPT-5 (latest generation)

3. **Prompt Engineering**: Structured prompt with:

   - QUS Framework definition
   - Defect examples for each criterion
   - JSON output format specification
   - Analysis instructions

4. **Evaluation Process**:
   - Each user story set evaluated by each model
   - Responses parsed and analyzed
   - Defects categorized by QUS criteria
   - Performance metrics calculated

### Metrics

- **Defect Detection Rate**: Number of defects found per story
- **Defect Type Distribution**: Breakdown by QUS criteria
- **Processing Time**: Time per story set
- **Model Consistency**: Agreement across models

## 📁 Repository Structure

```
llm-us-quality-xp26/
├── README.md                          # This file
├── DATA_README.md                     # Detailed data documentation
├── OVERVIEW.md                        # Quick start guide
├── columns.md                         # Output data structure
├── CITATION.cff                       # Citation metadata
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore patterns
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── run_experiment.sh                  # Reproduce experiment script
├── data/
│   ├── raw/                          # Original user story datasets
│   │   ├── g13-planningpoker.txt     # Planning Poker project (53 stories)
│   │   ├── g21-badcamp.txt           # BADCamp project (68 stories)
│   │   └── g28-zooniverse.txt        # Zooniverse project (47 stories)
│   └── processed/                    # Analysis results
│       └── data_processed.xlsx       # Model outputs and metrics
├── prompts/
│   └── prompt.txt                    # QUS Framework prompt template
├── src/
│   └── model_evaluation/
│       └── proces_userstories.py     # Main evaluation script
└── notebooks/                         # Analysis notebooks (optional)
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- pip package manager

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Ilusinusmate/llm-us-quality-xp26.git
cd llm-us-quality-xp26
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure API key**

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
API_KEY=your-openai-api-key-here
```

## 💻 Usage

### Running the Experiment

**Option 1: Using the shell script (recommended)**

```bash
chmod +x run_experiment.sh
./run_experiment.sh
```

**Option 2: Running Python directly**

```bash
python src/model_evaluation/proces_userstories.py
```

### What Happens

The script will:

1. Load user stories from `data/raw/`
2. Apply the QUS Framework prompt
3. Send requests to OpenAI API for each model
4. Collect responses with defect analysis
5. Save results to `data/processed/data_processed.xlsx`

### Expected Output

```
Processing user stories from g13-planningpoker.txt with model gpt-5-mini
Sending request to OpenAI with model gpt-5-mini
Successfully processed g13-planningpoker.txt with gpt-5-mini
Time taken: 12.34 seconds

Processing user stories from g21-badcamp.txt with model gpt-5-mini
...
```

### Customization

To modify the experiment:

1. **Change models**: Edit line 74 in `proces_userstories.py`

   ```python
   models = ["gpt-4o-mini", "gpt-4", "gpt-4o"]
   ```

2. **Add datasets**: Place `.txt` files in `data/raw/` and update line 75

3. **Modify prompt**: Edit `prompts/prompt.txt`

## 📊 Data Description

### Input Data

**User Story Format**: Plain text files with one story per line

Example:

```
As a moderator, I want to create a new game, so that I can start inviting estimators.
As an estimator, I want to join a game, so that I can participate.
```

### Output Data

**Excel file** (`data/processed/data_processed.xlsx`) with columns:

| Column       | Description                                  |
| ------------ | -------------------------------------------- |
| `user_story` | Complete text of all user stories in the set |
| `model`      | GPT model used (e.g., "gpt-4o-mini")         |
| `prompt`     | QUS Framework prompt template                |
| `response`   | JSON response with defect analysis           |
| `time`       | Processing time in seconds                   |

**Response JSON Structure**:

```json
{
  "defects": [
    {
      "story_id": 1,
      "story_text": "As a user...",
      "defect_type": "well_formed.no_means",
      "message": "Add what you want to achieve"
    }
  ],
  "summary": {
    "total_stories": 53,
    "total_defects": 12,
    "defect_types_count": {
      "well_formed.no_role": 3,
      "atomic.conjunctions": 5,
      "minimal.punctuation": 4
    }
  }
}
```

For detailed data documentation, see [DATA_README.md](DATA_README.md).

## 📈 Results

### Preliminary Findings

- **Total Stories Analyzed**: 168 (across 3 projects)
- **Models Evaluated**: 3 GPT variants
- **Total API Calls**: 9 (3 models × 3 datasets)

### Key Observations

1. **Defect Detection**: LLMs successfully identify syntactic defects (well-formedness, atomicity)
2. **Pragmatic Challenges**: Duplicate detection requires cross-story comparison
3. **Model Differences**: Newer models provide more detailed explanations
4. **Processing Time**: Varies by story set size and model

_Detailed results and statistical analysis are available in the full paper._

## 📚 Citation

If you use this work in your research, please cite:

### BibTeX

```bibtex
@article{llm-us-quality-xp26,
  title={Evaluating the Quality of User Stories: An Extended Comparative Study of Multiple LLMs and Rule-Based Tools},
  author={Silva, Izabella Ribeiro de Souza and Paiva, João Gabriel Salvador and Wagner, Danyllo Albuquerque and Gorgônio, Kyller and Perkusich, Angelo and Perkusich, Mirko},
  journal={Journal of Software and Systems},
  year={2025},
  publisher={Elsevier},
  note={Supplementary material available at: https://github.com/Ilusinusmate/llm-us-quality-xp26}
}
```

### APA

Silva, I. R. S., Paiva, J. G. S., Wagner, D. A., Gorgônio, K., Perkusich, A., & Perkusich, M. (2025). Evaluating the Quality of User Stories: An Extended Comparative Study of Multiple LLMs and Rule-Based Tools. _Journal of Software and Systems_. https://github.com/Ilusinusmate/llm-us-quality-xp26

### IEEE

I. R. S. Silva, J. G. S. Paiva, D. A. Wagner, K. Gorgônio, A. Perkusich, and M. Perkusich, "Evaluating the Quality of User Stories: An Extended Comparative Study of Multiple LLMs and Rule-Based Tools," _Journal of Software and Systems_, 2025.

### Citation File Format (CFF)

See [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

- **OpenAI API**: Subject to OpenAI's Terms of Use
- **User Story Datasets**: From open-source projects (see DATA_README.md for attributions)

## 👥 Authors

- **Izabella Ribeiro de Souza Silva** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande
- **João Gabriel Salvador Paiva** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande
- **Danyllo Albuquerque Wagner** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande
- **Kyller Gorgônio** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande
- **Angelo Perkusich** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande
- **Mirko Perkusich** - [ORCID: 0000-0000-0000-0000](https://orcid.org/0000-0000-0000-0000)
  - Federal University of Campina Grande

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new analysis'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📞 Contact

For questions or collaboration:

- Open an issue on GitHub
- Email the corresponding author: joao.gabriel.salvador.paiva@ccc.ufcg.edu.br

## 🙏 Acknowledgments

- OpenAI for providing API access
- Open-source projects for user story datasets

## 📖 Related Publications

1. Lucassen, G., et al. (2016). "The use and effectiveness of the Quality User Story framework in practice." _Requirements Engineering_, 21(2), 127-145.

---

**Repository**: https://github.com/Ilusinusmate/llm-us-quality-xp26  
**Paper**: available at xp26
**Last Updated**: November 2025
