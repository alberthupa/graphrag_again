"""Configurable entity type definitions for data engineering domain."""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EntityTypeConfig:
    """Configuration for an entity type including attributes and extraction hints."""
    
    name: str
    description: str
    required_attributes: List[str]
    optional_attributes: List[str]
    extraction_hints: List[str]
    example_patterns: List[str]


# Entity type configurations for data engineering domain
ENTITY_TYPE_CONFIGS: Dict[str, EntityTypeConfig] = {
    "KPI": EntityTypeConfig(
        name="KPI",
        description="Key Performance Indicator - measurable values that demonstrate effectiveness",
        required_attributes=["name", "definition"],
        optional_attributes=["calculation_method", "unit", "domain", "frequency", "target_value"],
        extraction_hints=[
            "Look for metrics that measure business performance",
            "Often mentioned with units like %, dollars, counts",
            "May include calculation formulas or methods",
            "Usually associated with business domains or departments"
        ],
        example_patterns=[
            "Revenue Growth Rate",
            "Customer Acquisition Cost",
            "Monthly Active Users",
            "Conversion Rate",
            "Average Order Value"
        ]
    ),
    
    "Table": EntityTypeConfig(
        name="Table",
        description="Database table or data structure containing organized information",
        required_attributes=["name"],
        optional_attributes=["description", "source_system", "schema", "row_count", "update_frequency"],
        extraction_hints=[
            "Database tables, data marts, or structured datasets",
            "Often have clear naming conventions",
            "May be described with their purpose and contents",
            "Can be associated with specific systems or databases"
        ],
        example_patterns=[
            "customer_transactions",
            "product_catalog",
            "sales_summary",
            "user_engagement_metrics",
            "financial_reporting"
        ]
    ),
    
    "Column": EntityTypeConfig(
        name="Column",
        description="Individual field or attribute within a table or dataset",
        required_attributes=["name", "type"],
        optional_attributes=["description", "table_reference", "constraints", "nullable", "default_value"],
        extraction_hints=[
            "Individual fields within tables or datasets",
            "Have specific data types (string, integer, date, etc.)",
            "May have constraints or validation rules",
            "Often described with their purpose and content"
        ],
        example_patterns=[
            "customer_id (integer)",
            "transaction_date (date)",
            "revenue_amount (decimal)",
            "product_name (varchar)",
            "is_active (boolean)"
        ]
    ),
    
    "Metric": EntityTypeConfig(
        name="Metric",
        description="Calculated measure or statistical value derived from data",
        required_attributes=["name", "formula"],
        optional_attributes=["dependencies", "calculation_frequency", "business_context", "owner"],
        extraction_hints=[
            "Calculated values derived from raw data",
            "Have specific formulas or calculation methods",
            "May depend on other metrics or data sources",
            "Often used for reporting and analysis"
        ],
        example_patterns=[
            "Average Session Duration = Total Session Time / Number of Sessions",
            "Churn Rate = Customers Lost / Total Customers",
            "Inventory Turnover = Cost of Goods Sold / Average Inventory"
        ]
    ),
    
    "DataSource": EntityTypeConfig(
        name="DataSource",
        description="Origin system or location where data is generated or stored",
        required_attributes=["name", "type"],
        optional_attributes=["connection_info", "refresh_schedule", "owner", "documentation_url"],
        extraction_hints=[
            "Systems that generate or store data",
            "Can be databases, APIs, files, or external services",
            "Often have connection details or access methods",
            "May have refresh schedules or update frequencies"
        ],
        example_patterns=[
            "Salesforce CRM",
            "Google Analytics",
            "MySQL Production Database",
            "AWS S3 Data Lake",
            "Shopify API"
        ]
    ),
    
    "Domain": EntityTypeConfig(
        name="Domain",
        description="Business area or functional domain that groups related entities",
        required_attributes=["name"],
        optional_attributes=["description", "owner", "stakeholders"],
        extraction_hints=[
            "Business areas or functional groups",
            "Organizational departments or teams",
            "Subject areas that group related data and metrics"
        ],
        example_patterns=[
            "Sales & Marketing",
            "Customer Experience",
            "Operations",
            "Finance & Accounting",
            "Product Development"
        ]
    ),
    
    "Formula": EntityTypeConfig(
        name="Formula",
        description="Mathematical expression or calculation method",
        required_attributes=["expression"],
        optional_attributes=["variables", "constraints", "description"],
        extraction_hints=[
            "Mathematical expressions with variables",
            "Calculation methods or algorithms",
            "May include operators, functions, and conditions"
        ],
        example_patterns=[
            "SUM(revenue) / COUNT(customers)",
            "(New Customers / Total Customers) * 100",
            "MAX(transaction_date) - MIN(transaction_date)"
        ]
    ),
    
    "Definition": EntityTypeConfig(
        name="Definition",
        description="Explanation or specification of what something means or represents",
        required_attributes=["text"],
        optional_attributes=["source", "version", "last_updated"],
        extraction_hints=[
            "Explanatory text that defines concepts",
            "Business definitions for terms and metrics",
            "May include examples or clarifications"
        ],
        example_patterns=[
            "Customer Lifetime Value is the total revenue a customer generates over their relationship with the company",
            "Active users are defined as users who have logged in within the past 30 days"
        ]
    )
}


def get_entity_config(entity_type: str) -> EntityTypeConfig:
    """Get configuration for a specific entity type."""
    return ENTITY_TYPE_CONFIGS.get(entity_type.upper(), None)


def get_all_entity_types() -> List[str]:
    """Get list of all configured entity types."""
    return list(ENTITY_TYPE_CONFIGS.keys())


def get_extraction_prompt_context() -> str:
    """Generate context for extraction prompts based on entity configurations."""
    context_parts = []
    
    for entity_type, config in ENTITY_TYPE_CONFIGS.items():
        context_parts.append(f"**{entity_type}**: {config.description}")
        context_parts.append(f"  - Required: {', '.join(config.required_attributes)}")
        context_parts.append(f"  - Examples: {', '.join(config.example_patterns[:3])}")
        context_parts.append("")
    
    return "\n".join(context_parts)