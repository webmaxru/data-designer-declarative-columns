# Example YAML Configurations

This folder contains YAML configurations converted from the official Data Designer recipes.

## Available Examples

| File | Description |
|------|-------------|
| [product_reviews.yaml](product_reviews.yaml) | **Comprehensive example** - E-commerce product reviews with all column types |
| [text_to_python.yaml](text_to_python.yaml) | Python code generation with quality scoring |
| [text_to_sql.yaml](text_to_sql.yaml) | SQL query generation with database context |
| [multi_turn_chat.yaml](multi_turn_chat.yaml) | Multi-turn conversations with toxicity evaluation |
| [product_info_qa.yaml](product_info_qa.yaml) | Product Q&A with hallucination detection |
| [basic_mcp.yaml](basic_mcp.yaml) | Basic MCP tool use (columns + tool configs) |
| [pdf_qa.yaml](pdf_qa.yaml) | Document Q&A with BM25 search (columns + tool configs) |

## Usage

### Standard Examples (No MCP)

```python
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner

# Load any example
config = DeclarativeColumnsConfig(file="examples/text_to_python.yaml")

# Add to builder and run
data_designer = DataDesigner()
config_builder = dd.DataDesignerConfigBuilder()
config.add_columns_to_builder(config_builder)

preview = data_designer.preview(config_builder, num_records=3)
preview.display_sample_record()
```

### MCP Examples (With Tool Use)

MCP examples include `tool_configs` in the YAML. Use `get_tool_configs()` when creating the builder:

```python
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner

# Load MCP example
config = DeclarativeColumnsConfig(file="examples/basic_mcp.yaml")

# Create builder WITH tool configs from YAML
config_builder = dd.DataDesignerConfigBuilder(tool_configs=config.get_tool_configs())
config.add_columns_to_builder(config_builder)

# You must still define the MCP provider in Python
mcp_provider = dd.LocalStdioMCPProvider(
    name="basic-tools",
    command=sys.executable,
    args=["your_mcp_server.py", "serve"],
)

# Create DataDesigner with the MCP provider
data_designer = DataDesigner(mcp_providers=[mcp_provider])
preview = data_designer.preview(config_builder, num_records=2)
preview.display_sample_record()
```

## Notes

- **Model Alias**: All examples use `nvidia-text` as the default model alias. Change this to match your configured models.
- **MCP Server Code**: The MCP tool implementations (e.g., `@mcp_server.tool()` functions) must still be written in Python. The YAML only configures the *column definitions* and *tool configs*.
- **Structured Outputs**: The `llm-structured` column type uses JSON Schema format for `output_format` instead of Pydantic models.

## Column Types Used

These examples demonstrate all major column types:

- `sampler` - UUID, Category, Subcategory, Uniform, Gaussian, DateTime, Person (Faker)
- `llm-text` - Text generation with prompts
- `llm-code` - Code generation (Python, SQL)
- `llm-structured` - Structured JSON output with schema
- `llm-judge` - Quality evaluation with scoring rubrics
- `expression` - Jinja2 expressions for derived values
- `validation` - Code validation (Python, SQL syntax checking)

The [product_reviews.yaml](product_reviews.yaml) example demonstrates all of these column types in a single configuration.
