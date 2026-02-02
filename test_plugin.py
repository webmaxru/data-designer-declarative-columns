# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Example script demonstrating the declarative-columns utility.

This script shows how to use DeclarativeColumnsConfig to load
multiple column definitions from a YAML file.

Usage:
    # First install the package
    cd data-designer-declarative-columns
    uv pip install -e .

    # Run this example
    python test_plugin.py
"""

from __future__ import annotations

from pathlib import Path

# Import the config class
from data_designer_declarative_columns import DeclarativeColumnsConfig

import data_designer.config as dd
from data_designer.interface import DataDesigner


def main() -> None:
    """Demonstrate the declarative-columns utility."""
    print("=" * 60)
    print("Data Designer Declarative Columns Demo")
    print("=" * 60)

    # Initialize Data Designer
    data_designer = DataDesigner()
    builder = dd.DataDesignerConfigBuilder()

    # Load columns from YAML file
    yaml_file = Path(__file__).parent.parent / "text_to_python.yaml"
    print(f"\nLoading columns from: {yaml_file}")

    declarative_config = DeclarativeColumnsConfig(
        name="text_to_python",
        file=str(yaml_file),
    )

    # Show what was loaded
    print(f"\nLoaded {len(declarative_config)} columns:")
    for col in declarative_config.columns:
        print(f"  - {col['name']} ({col['column_type']})")

    # Add all columns to the builder
    print("\nAdding columns to builder...")
    declarative_config.add_columns_to_builder(builder)

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print("""
The columns have been loaded and added to the config builder.
To run a preview, you'll need a valid model configuration with
the alias 'default' (or update the YAML to use a different alias).
""")


if __name__ == "__main__":
    main()
