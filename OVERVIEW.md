# Quick Start Guide

Welcome to the **Evaluating the Quality of User Stories** repository! This guide will help you get started quickly.

## 🎯 What is This?

This repository contains supplementary materials for an extended comparative study evaluating the quality of agile user stories using Large Language Models (GPT-5, GPT-5-mini, GPT-4) and the Quality User Story (QUS) Framework. It automatically detects 7 types of quality defects in user stories.

## ⚡ Quick Start (5 minutes)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/llm-us-quality-xp26.git
cd llm-us-quality-xp26
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run Experiment

```bash
./run_experiment.sh
```

That's it! Results will be in `data/processed/data_processed.xlsx`.

## 📊 What You Get

### Input

- 3 datasets with 168 user stories from real projects
- QUS Framework prompt template

### Output

- Quality defect analysis from GPT-5, GPT-5-mini, and GPT-4
- Defect categorization (7 types)
- Processing time metrics
- Comparative performance analysis

### Example Result

```json
{
  "defects": [
    {
      "story_id": 4,
      "defect_type": "atomic.conjunctions",
      "message": "Split into separate stories"
    }
  ],
  "summary": {
    "total_stories": 53,
    "total_defects": 8
  }
}
```

## 🔍 Key Features

✅ **Automated Analysis**: No manual review needed  
✅ **Multi-Model**: Compare GPT-5, GPT-5-mini, GPT-4  
✅ **Structured Output**: JSON format for easy parsing  
✅ **Reproducible**: Complete scripts and data included  
✅ **Well-Documented**: Comprehensive guides and examples

## 📚 Documentation

| File                             | Description               |
| -------------------------------- | ------------------------- |
| [README.md](README.md)           | Complete project overview |
| [DATA_README.md](DATA_README.md) | Data documentation        |
| [columns.md](columns.md)         | Output structure          |
| [CITATION.cff](CITATION.cff)     | Citation metadata         |

## 🎓 QUS Framework (7 Criteria)

**Syntactic Quality**

1. ❌ `well_formed.no_role` - Missing role
2. ❌ `well_formed.no_means` - Missing action
3. ❌ `atomic.conjunctions` - Multiple features
4. ❌ `minimal.punctuation` - Excessive notes
5. ❌ `minimal.brackets` - Unnecessary brackets

**Pragmatic Quality** 6. ❌ `unique.identical` - Duplicates 7. ❌ `uniform.uniform` - Inconsistent phrasing

## 📁 Repository Structure

```
llm-us-quality-xp26/
├── data/
│   ├── raw/              # 3 user story datasets
│   └── processed/        # Analysis results
├── prompts/              # QUS Framework prompt
├── src/                  # Evaluation script
├── run_experiment.sh     # Reproduction script
└── *.md                  # Documentation
```

## 💻 Usage Examples

### Analyze Your Own Stories

1. Create a text file with your stories (one per line)
2. Place in `data/raw/`
3. Edit `src/model_evaluation/proces_userstories.py`:
   ```python
   user_stories = ["your-file.txt"]
   ```
4. Run: `python src/model_evaluation/proces_userstories.py`

### Change Models

Edit line 74 in `proces_userstories.py`:

```python
models = ["gpt-4o-mini"]  # Use only one model
```

### Parse Results

```python
import pandas as pd
import json

df = pd.read_excel('data/processed/data_processed.xlsx')
for idx, row in df.iterrows():
    response = json.loads(row['response'])
    print(f"Model: {row['model']}")
    print(f"Defects: {response['summary']['total_defects']}")
```

## 📈 Expected Results

- **Processing Time**: 5-30 seconds per dataset
- **API Cost**: ~$0.50-$2.00 for full experiment
- **Defects Found**: Typically 10-20% of stories have defects

## 🚨 Common Issues

### "API key not found"

- Check `.env` file exists
- Verify `API_KEY=...` is set correctly

### "Module not found"

- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### "Rate limit exceeded"

- Wait a few minutes
- Use `gpt-4o-mini` for lower rate limits

## 🤝 Contributing

Found a bug? Have a suggestion?

1. Open an issue on GitHub
2. Submit a pull request
3. Email: joao.gabriel.salvador.paiva@ccc.ufcg.edu.br

## 📖 Citation

```bibtex
@article{llm-us-quality-xp26,
  title={Evaluating the Quality of User Stories: An Extended Comparative Study of Multiple LLMs and Rule-Based Tools},
  author={Silva, Izabella Ribeiro de Souza and Paiva, João Gabriel Salvador and Wagner, Danyllo Albuquerque and Gorgônio, Kyller and Perkusich, Angelo and Perkusich, Mirko},
  journal={Journal of Software and Systems},
  year={2025}
}
```

## 🔗 Links

- **Repository**: https://github.com/Ilusinusmate/llm-us-quality-xp26
- **Paper**: [Coming soon]
- **Issues**: https://github.com/Ilusinusmate/llm-us-quality-xp26/issues

## 📞 Support

Need help?

- 📧 Email: joao.gabriel.salvador.paiva@ccc.ufcg.edu.br
- 💬 GitHub Issues: [Open an issue](https://github.com/Ilusinusmate/llm-us-quality-xp26/issues)
- 📚 Full docs: [README.md](README.md)

---

**Ready to start?** Run `./run_experiment.sh` and explore the results! 🚀
