# Data Designer Declarative Columns Plugin

A Data Designer utility that allows loading multiple column configurations from YAML.

## Features

- **Multi-column YAML**: Load entire column configurations from a YAML file or inline string
- **All column types supported**: sampler, llm-text, llm-code, llm-structured, llm-judge, expression, validation
- **MCP Tool Configs**: Define `tool_configs` in YAML for MCP tool use workflows
- **Reusable configurations**: Share column definitions across projects via YAML files
- **Full parity with Python API**: YAML configs are equivalent to programmatic `add_column()` calls

## Installation

Install from PyPI:

```bash
pip install data-designer-declarative-columns
```

Or with uv:

```bash
uv add data-designer-declarative-columns
```

For development (editable install):

```bash
git clone https://github.com/webmaxru/data-designer-declarative-columns.git
cd data-designer-declarative-columns
pip install -e .
```

## Usage

### From YAML File

```python
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner

data_designer = DataDesigner()
config_builder = dd.DataDesignerConfigBuilder()

# Load columns from YAML file
config = DeclarativeColumnsConfig(file="examples/product_reviews.yaml")
config.add_columns_to_builder(config_builder)

# Run preview
preview_results = data_designer.preview(config_builder=config_builder, num_records=3)
preview_results.display_sample_record()
```

### From Inline YAML

```python
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner

data_designer = DataDesigner()
config_builder = dd.DataDesignerConfigBuilder()

# Define columns inline (excerpt from product_reviews.yaml)
config = DeclarativeColumnsConfig(yaml_content="""
columns:
  - name: product_category
    column_type: sampler
    sampler_type: category
    params:
      values: [Electronics, Clothing, Books, Home & Garden]
      weights: [3, 2, 2, 1]

  - name: price
    column_type: sampler
    sampler_type: uniform
    params:
      low: 9.99
      high: 499.99

  - name: customer
    column_type: sampler
    sampler_type: person_from_faker
    params:
      locale: en_US
      age_range: [18, 65]

  - name: review
    column_type: llm-text
    model_alias: nvidia-text
    prompt: |
      Write a realistic customer review for a product in the {{ product_category }} category.
      The product costs ${{ price | round(2) }}.

  - name: customer_name
    column_type: expression
    expr: "{{ customer.first_name }} {{ customer.last_name }}"
""")

config.add_columns_to_builder(config_builder)
preview_results = data_designer.preview(config_builder=config_builder, num_records=3)
preview_results.display_sample_record()
```

### With MCP Tool Configs

For MCP tool use workflows, define `tool_configs` in the YAML and use `get_tool_configs()`:

```python
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner

# Load configuration with tool_configs
config = DeclarativeColumnsConfig(file="examples/basic_mcp.yaml")

# Create builder WITH tool configs from YAML
config_builder = dd.DataDesignerConfigBuilder(tool_configs=config.get_tool_configs())
config.add_columns_to_builder(config_builder)

# Define MCP provider (server code must still be Python)
mcp_provider = dd.LocalStdioMCPProvider(
    name="basic-tools",
    command=sys.executable,
    args=["your_mcp_server.py", "serve"],
)

# Create DataDesigner with MCP provider
data_designer = DataDesigner(mcp_providers=[mcp_provider])
preview_results = data_designer.preview(config_builder, num_records=2)
```

**YAML with tool_configs**:
```yaml
tool_configs:
  - tool_alias: basic-tools
    providers: [basic-tools]
    allow_tools: [get_fact, add_numbers]
    max_tool_call_turns: 5
    timeout_sec: 30.0

columns:
  - name: topic
    column_type: sampler
    sampler_type: category
    params:
      values: [python, earth, water]

  - name: fact_response
    column_type: llm-text
    model_alias: nvidia-text
    prompt: "Use the get_fact tool to look up '{{ topic }}'"
    tool_alias: basic-tools
    with_trace: true
```

### YAML Configuration Format

**product_reviews.yaml** (excerpt):
```yaml
columns:
  - name: product_category
    column_type: sampler
    sampler_type: category
    params:
      values: [Electronics, Clothing, Books, Home & Garden]
      weights: [3, 2, 2, 1]

  - name: customer
    column_type: sampler
    sampler_type: person_from_faker
    params:
      locale: en_US
      age_range: [18, 65]

  - name: review
    column_type: llm-text
    model_alias: nvidia-text
    prompt: |
      Write a realistic customer review for a {{ product_subcategory }} 
      in the {{ product_category }} category.

  - name: review_analysis
    column_type: llm-structured
    model_alias: nvidia-text
    prompt: |
      Analyze this product review and extract structured information:
      Review: "{{ review }}"
    output_format:
      type: object
      properties:
        sentiment:
          type: string
          enum: [positive, neutral, negative]
        would_recommend:
          type: boolean
      required: [sentiment, would_recommend]
```

### Inspecting Loaded Columns

```python
config = DeclarativeColumnsConfig(file="examples/product_reviews.yaml")

# Get list of column names
print(config.get_column_names())
# ['request_id', 'product_category', 'product_subcategory', 'price', ...]

# Get number of columns
print(len(config))
# 14

# Access raw column definitions
for col in config.columns:
    print(f"{col['name']}: {col['column_type']}")
```

## Supported Column Types

| Column Type | Description | Example Fields |
|-------------|-------------|----------------|
| `sampler` | Built-in samplers (UUID, Category, Uniform, Person, etc.) | `sampler_type`, `params` |
| `llm-text` | LLM text generation with Jinja2 templating | `model_alias`, `prompt`, `system_prompt` |
| `llm-code` | Code generation with language specification | `model_alias`, `code_lang`, `prompt` |
| `llm-structured` | Structured JSON generation with schema | `model_alias`, `prompt`, `output_schema` |
| `llm-judge` | Quality assessment with scoring rubrics | `model_alias`, `prompt`, `scores` |
| `expression` | Expression-based derived columns | `expr` |
| `validation` | Validation results (Python, SQL, Code validators) | `validator_type`, `target_columns`, `validator_params` |

## Examples

See the [`examples/`](examples/) folder for complete YAML configurations:

- **[product_reviews.yaml](examples/product_reviews.yaml)** - Comprehensive example with all column types:
  - Samplers: UUID, Category, Subcategory, Uniform, Gaussian, DateTime, Person (Faker)
  - LLM Text: Product review generation
  - LLM Code: SQL query generation
  - LLM Structured: Review sentiment analysis
  - LLM Judge: Review quality scoring
  - Expressions: Derived values (word count, price tier, customer name)

- **[text_to_python.yaml](examples/text_to_python.yaml)** - Python code generation with validation
- **[text_to_sql.yaml](examples/text_to_sql.yaml)** - SQL query generation
- **[multi_turn_chat.yaml](examples/multi_turn_chat.yaml)** - Multi-turn conversations
- **[product_info_qa.yaml](examples/product_info_qa.yaml)** - Product Q&A
- **[basic_mcp.yaml](examples/basic_mcp.yaml)** - MCP tool use
- **[pdf_qa.yaml](examples/pdf_qa.yaml)** - Document Q&A with MCP

## License

Apache-2.0
