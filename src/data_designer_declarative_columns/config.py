# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Data Designer Declarative Columns Plugin - Configuration

This module defines the configuration class for loading multiple columns from YAML.
It provides a way to define entire column configurations declaratively in YAML format.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class DeclarativeColumnsConfig(BaseModel):
    """Configuration for loading multiple columns from YAML.

    This class allows loading a complete column configuration from either:
    - A YAML file (via `file` parameter)
    - Inline YAML content (via `yaml_content` parameter)

    Each column is defined with its type (sampler, llm-text, llm-code, etc.)
    and all associated parameters.

    The YAML should follow the Data Designer column configuration format:
    ```yaml
    # Optional: Tool configurations for MCP tool use
    tool_configs:
      - tool_alias: my-tools
        providers: [my-mcp-server]
        allow_tools: [search, list_items]
        max_tool_call_turns: 5
        timeout_sec: 30.0

    columns:
      - name: industry_sector
        column_type: sampler
        sampler_type: category
        params:
          values:
            - Healthcare
            - Finance

      - name: instruction
        column_type: llm-text
        model_alias: default
        prompt: "Generate an instruction for {{ industry_sector }}"
    ```

    Attributes:
        file: Path to the YAML file containing column definitions.
        yaml_content: Inline YAML string containing column definitions.
        tool_configs: Parsed tool configurations (for MCP tool use).
        columns: Parsed column definitions (populated after loading).

    Examples:
        From file:
        ```python
        config = DeclarativeColumnsConfig(file="text_to_python.yaml")
        ```

        From inline YAML:
        ```python
        config = DeclarativeColumnsConfig(yaml_content='''
        columns:
          - name: category
            column_type: sampler
            sampler_type: category
            params:
              values: [A, B, C]
        ''')
        ```

        With tool configs (MCP):
        ```python
        config = DeclarativeColumnsConfig(file="mcp_recipe.yaml")
        # Use get_tool_configs() when creating the builder:
        builder = dd.DataDesignerConfigBuilder(tool_configs=config.get_tool_configs())
        config.add_columns_to_builder(builder)
        ```
    """

    file: str | None = Field(
        default=None,
        description="Path to YAML file containing column definitions",
    )
    yaml_content: str | None = Field(
        default=None,
        description="Inline YAML string containing column definitions",
    )
    tool_configs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parsed tool configurations for MCP tool use",
    )
    columns: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parsed column definitions from the YAML",
    )
    _yaml_loaded: bool = False

    class Config:
        arbitrary_types_allowed = True

    @model_validator(mode="after")
    def load_yaml(self) -> Self:
        """Load and parse YAML from file or inline content."""
        if self._yaml_loaded:
            return self

        # Validate that exactly one source is provided
        if self.file is None and self.yaml_content is None:
            raise ValueError("Either 'file' or 'yaml_content' must be provided")
        if self.file is not None and self.yaml_content is not None:
            raise ValueError("Cannot specify both 'file' and 'yaml_content' - use one or the other")

        # Load YAML from appropriate source
        if self.file is not None:
            file_path = Path(self.file)
            if not file_path.exists():
                raise FileNotFoundError(f"YAML configuration file not found: {file_path}")

            with file_path.open("r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Failed to parse YAML file {file_path}: {e}") from e

            source_desc = f"file {file_path}"
        else:
            try:
                data = yaml.safe_load(self.yaml_content)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse inline YAML: {e}") from e

            source_desc = "inline YAML"

        if data is None:
            raise ValueError(f"YAML is empty: {source_desc}")

        # Extract columns from the YAML data
        if isinstance(data, dict) and "columns" in data:
            self.columns = data["columns"]
            # Also extract tool_configs if present
            if "tool_configs" in data:
                self.tool_configs = data["tool_configs"]
        elif isinstance(data, list):
            # Support YAML that is just a list of columns
            self.columns = data
        else:
            raise ValueError(
                f"YAML ({source_desc}) must contain a 'columns' key with a list, "
                "or be a list of column definitions"
            )

        if not self.columns:
            raise ValueError(f"No columns defined in {source_desc}")

        # Validate each column has required fields
        for i, col in enumerate(self.columns):
            if "name" not in col:
                raise ValueError(f"Column at index {i} is missing required 'name' field")
            if "column_type" not in col:
                raise ValueError(
                    f"Column '{col.get('name', f'index {i}')}' is missing required 'column_type' field"
                )

        object.__setattr__(self, "_yaml_loaded", True)
        return self

    def add_columns_to_builder(
        self,
        config_builder: Any,
        *,
        verbose: bool = True,
    ) -> None:
        """Add all columns from the YAML file to a DataDesignerConfigBuilder.

        Args:
            config_builder: The DataDesignerConfigBuilder instance to add columns to.
            verbose: If True, print status messages for each column added.

        Raises:
            ValueError: If a column definition is invalid.
        """
        for column_def in self.columns:
            kwargs = column_def.copy()
            name = kwargs.pop("name")
            column_type = kwargs.pop("column_type")

            try:
                config_builder.add_column(name=name, column_type=column_type, **kwargs)
                if verbose:
                    print(f"  [+] Added column: {name} ({column_type})")
            except Exception as e:
                raise ValueError(f"Failed to add column '{name}': {e}") from e

    def get_column_names(self) -> list[str]:
        """Return the names of all columns defined in the YAML file.

        Returns:
            List of column names.
        """
        return [col["name"] for col in self.columns]

    def get_tool_configs(self) -> list[Any]:
        """Return ToolConfig objects for use with DataDesignerConfigBuilder.

        This method converts the raw tool_configs dicts from YAML into
        proper dd.ToolConfig objects that can be passed to the builder.

        Returns:
            List of ToolConfig objects, or empty list if no tool configs defined.

        Example:
            ```python
            config = DeclarativeColumnsConfig(file="mcp_recipe.yaml")
            builder = dd.DataDesignerConfigBuilder(tool_configs=config.get_tool_configs())
            config.add_columns_to_builder(builder)
            ```
        """
        import data_designer.config as dd

        return [dd.ToolConfig(**tc) for tc in self.tool_configs]

    def has_tool_configs(self) -> bool:
        """Check if the configuration includes tool configs for MCP.

        Returns:
            True if tool_configs are defined, False otherwise.
        """
        return len(self.tool_configs) > 0

    def __len__(self) -> int:
        """Return the number of columns defined."""
        return len(self.columns)
