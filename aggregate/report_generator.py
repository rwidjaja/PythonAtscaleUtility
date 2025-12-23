# aggregate/report_generator.py
import csv
import os
from datetime import datetime
from typing import Dict, List
from .api_client import AtScaleAPIClient


class ReportGenerator:
    def __init__(self):
        self.api_client = AtScaleAPIClient()
    
    def export_cube_aggregates_csv(self, cube_data: Dict) -> str:
        """Export cube aggregates to CSV file"""
        response = self.api_client.get_aggregates_by_cube(
            cube_data["project_id"], 
            cube_data["cube_id"]
        )
        
        aggregates_data = response.get("response", {}).get("data", [])
        
        if not aggregates_data:
            raise Exception("No aggregates found to export.")
        
        # Create filename with timestamp and cube name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cube_name = "".join(c for c in cube_data['display'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"aggregates_{safe_cube_name}_{timestamp}.csv"
        
        # Define CSV columns
        fieldnames = [
            "aggregate_id", "aggregate_name", "type", "subtype", 
            "status", "rows", "build_duration_ms", "avg_build_duration_ms",
            "query_utilization", "last_query_time", "created_at",
            "table_name", "table_schema", "batch_id", "connection_id",
            "key_count", "measure_count", "dimension_count", "total_attributes"
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for agg in aggregates_data:
                latest_instance = agg.get("latest_instance", {})
                instance_stats = latest_instance.get("stats", {})
                agg_stats = agg.get("stats", {})
                
                # Count attribute types
                attributes = agg.get("attributes", [])
                key_count = sum(1 for a in attributes if a.get("type") == "key")
                measure_count = sum(1 for a in attributes if a.get("type") == "measure")
                dimension_count = sum(1 for a in attributes if a.get("type") == "dimension")
                
                row = {
                    "aggregate_id": agg.get("id", ""),
                    "aggregate_name": agg.get("name", ""),
                    "type": agg.get("type", ""),
                    "subtype": agg.get("subtype", ""),
                    "status": latest_instance.get("status", ""),
                    "rows": instance_stats.get("number_of_rows", 0),
                    "build_duration_ms": instance_stats.get("build_duration", 0),
                    "avg_build_duration_ms": agg_stats.get("average_build_duration", 0),
                    "query_utilization": agg_stats.get("query_utilization", 0),
                    "last_query_time": agg_stats.get("most_recent_query", ""),
                    "created_at": agg_stats.get("created_at", ""),
                    "table_name": latest_instance.get("table_name", ""),
                    "table_schema": latest_instance.get("table_schema", ""),
                    "batch_id": latest_instance.get("batch_id", ""),
                    "connection_id": latest_instance.get("connection_id", ""),
                    "key_count": key_count,
                    "measure_count": measure_count,
                    "dimension_count": dimension_count,
                    "total_attributes": len(attributes)
                }
                writer.writerow(row)
        
        return filename
    
    def show_cube_aggregate_statistics(self, cube_data: Dict) -> str:
        """Show aggregate statistics for a specific cube - returns formatted string"""
        response = self.api_client.get_aggregates_by_cube(
            cube_data["project_id"], 
            cube_data["cube_id"]
        )
        
        aggregates_data = response.get("response", {}).get("data", [])
        
        if not aggregates_data:
            return "No aggregates found."
        
        # Generate statistics string
        output = []
        output.append(f"AGGREGATE STATISTICS - {cube_data['display']}")
        output.append("=" * 60)
        output.append(f"Total Aggregates: {len(aggregates_data)}")
        
        # Type breakdown
        type_count = {}
        for agg in aggregates_data:
            agg_type = agg.get("type", "unknown")
            type_count[agg_type] = type_count.get(agg_type, 0) + 1
        
        if type_count:
            output.append("\nType Breakdown:")
            for agg_type, count in sorted(type_count.items()):
                percentage = (count / len(aggregates_data)) * 100
                output.append(f"  {agg_type.replace('_', ' ').title():25} {count:3d} ({percentage:.1f}%)")
        
        return "\n".join(output)
    
    def check_cube_aggregate_health(self, cube_data: Dict) -> str:
        """Check aggregate health for a specific cube - returns formatted string"""
        response = self.api_client.get_aggregates_by_cube(
            cube_data["project_id"], 
            cube_data["cube_id"]
        )
        
        aggregates_data = response.get("response", {}).get("data", [])
        
        if not aggregates_data:
            return "No aggregates found."
        
        # Generate health report
        output = []
        output.append(f"AGGREGATE HEALTH CHECK - {cube_data['display']}")
        output.append("=" * 60)
        
        issues = []
        warnings = []
        
        for agg in aggregates_data:
            agg_id = agg.get("id", "Unknown")[:12] + "..."
            status = agg.get("latest_instance", {}).get("status", "").lower()
            rows = agg.get("latest_instance", {}).get("stats", {}).get("number_of_rows", 0)
            
            # Check for inactive aggregates
            if status != "active":
                issues.append(f"✗ {agg_id}: Status is '{status}'")
            
            # Check for aggregates with 0 rows
            if rows == 0:
                warnings.append(f"⚠ {agg_id}: Has 0 rows")
        
        output.append(f"\nIssues Found ({len(issues)}):")
        if issues:
            for issue in issues[:10]:
                output.append(f"  {issue}")
        else:
            output.append("  ✓ No critical issues found")
        
        output.append(f"\nWarnings ({len(warnings)}):")
        if warnings:
            for warning in warnings[:10]:
                output.append(f"  {warning}")
        else:
            output.append("  ✓ No warnings")
        
        return "\n".join(output)
    
    def show_detailed_analysis(self, cube_data: Dict) -> str:
        """Show detailed analysis of aggregates - returns formatted string"""
        response = self.api_client.get_aggregates_by_cube(
            cube_data["project_id"], 
            cube_data["cube_id"]
        )
        
        aggregates_data = response.get("response", {}).get("data", [])
        
        if not aggregates_data:
            return "No aggregates found."
        
        # Generate analysis
        output = []
        output.append(f"DETAILED ANALYSIS - {cube_data['display']}")
        output.append("=" * 60)
        output.append(f"Total Aggregates: {len(aggregates_data)}")
        
        # Attribute analysis
        total_attributes = 0
        key_attributes = 0
        measure_attributes = 0
        dimension_attributes = 0
        
        for agg in aggregates_data:
            attributes = agg.get("attributes", [])
            total_attributes += len(attributes)
            
            for attr in attributes:
                attr_type = attr.get("type", "")
                if attr_type == "key":
                    key_attributes += 1
                elif attr_type == "measure":
                    measure_attributes += 1
                elif attr_type == "dimension":
                    dimension_attributes += 1
        
        output.append(f"\nAttribute Analysis:")
        output.append(f"  Total Attributes:       {total_attributes:,}")
        output.append(f"  Key Attributes:         {key_attributes:,}")
        output.append(f"  Measure Attributes:     {measure_attributes:,}")
        output.append(f"  Dimension Attributes:   {dimension_attributes:,}")
        
        return "\n".join(output)