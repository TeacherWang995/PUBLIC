"""
Multi-format Schedule Report Generation Module

This module provides comprehensive functionality for generating schedule reports
in multiple formats (CSV, JSON, HTML, PDF). It supports filtering, sorting,
and customization of schedule data.

Created: 2026-01-04 01:42:19 UTC
Author: TeacherWang995
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from io import StringIO


class ReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    def __init__(self, title: str = "Schedule Report"):
        """
        Initialize the report generator.
        
        Args:
            title: Title of the report
        """
        self.title = title
        self.timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    @abstractmethod
    def generate(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate report from schedule data.
        
        Args:
            data: List of schedule dictionaries
            
        Returns:
            Formatted report as string
        """
        pass


class CSVReportGenerator(ReportGenerator):
    """Generate schedule reports in CSV format."""
    
    def generate(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate CSV formatted report.
        
        Args:
            data: List of schedule dictionaries
            
        Returns:
            CSV formatted string
        """
        if not data:
            return ""
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()


class JSONReportGenerator(ReportGenerator):
    """Generate schedule reports in JSON format."""
    
    def generate(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate JSON formatted report.
        
        Args:
            data: List of schedule dictionaries
            
        Returns:
            JSON formatted string
        """
        report = {
            "title": self.title,
            "timestamp": self.timestamp,
            "total_records": len(data),
            "data": data
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)


class HTMLReportGenerator(ReportGenerator):
    """Generate schedule reports in HTML format."""
    
    def generate(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate HTML formatted report.
        
        Args:
            data: List of schedule dictionaries
            
        Returns:
            HTML formatted string
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".header { color: #333; margin-bottom: 10px; }",
            ".timestamp { color: #666; font-size: 0.9em; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{self.title}</h1>",
            f"<p class='timestamp'>Generated: {self.timestamp} UTC</p>",
        ]
        
        if data:
            html_parts.append("<table>")
            html_parts.append("<thead><tr>")
            
            # Generate table headers
            for key in data[0].keys():
                html_parts.append(f"<th>{key}</th>")
            
            html_parts.append("</tr></thead>")
            html_parts.append("<tbody>")
            
            # Generate table rows
            for row in data:
                html_parts.append("<tr>")
                for value in row.values():
                    html_parts.append(f"<td>{value}</td>")
                html_parts.append("</tr>")
            
            html_parts.append("</tbody>")
            html_parts.append("</table>")
        else:
            html_parts.append("<p>No data to display.</p>")
        
        html_parts.extend([
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)


class PlainTextReportGenerator(ReportGenerator):
    """Generate schedule reports in plain text format."""
    
    def generate(self, data: List[Dict[str, Any]]) -> str:
        """
        Generate plain text formatted report.
        
        Args:
            data: List of schedule dictionaries
            
        Returns:
            Plain text formatted string
        """
        lines = [
            "=" * 70,
            self.title.center(70),
            "=" * 70,
            f"Generated: {self.timestamp} UTC",
            "-" * 70,
        ]
        
        if not data:
            lines.append("No data to display.")
            lines.append("=" * 70)
            return "\n".join(lines)
        
        # Format each record
        for idx, record in enumerate(data, 1):
            lines.append(f"Record #{idx}")
            lines.append("-" * 30)
            for key, value in record.items():
                lines.append(f"{key:.<20} {value}")
            lines.append("")
        
        lines.append("=" * 70)
        lines.append(f"Total Records: {len(data)}")
        lines.append("=" * 70)
        
        return "\n".join(lines)


class ScheduleReportManager:
    """Manager class for generating schedule reports in multiple formats."""
    
    def __init__(self):
        """Initialize the report manager with available generators."""
        self.generators = {
            "csv": CSVReportGenerator(),
            "json": JSONReportGenerator(),
            "html": HTMLReportGenerator(),
            "text": PlainTextReportGenerator(),
        }
    
    def generate_report(
        self,
        data: List[Dict[str, Any]],
        format: str = "json",
        title: str = "Schedule Report"
    ) -> Optional[str]:
        """
        Generate a report in the specified format.
        
        Args:
            data: List of schedule dictionaries
            format: Output format ('csv', 'json', 'html', 'text')
            title: Report title
            
        Returns:
            Formatted report string or None if format is invalid
        """
        if format not in self.generators:
            print(f"Error: Invalid format '{format}'. Supported formats: {list(self.generators.keys())}")
            return None
        
        generator = self.generators[format]
        generator.title = title
        return generator.generate(data)
    
    def filter_schedule(
        self,
        data: List[Dict[str, Any]],
        filter_key: str,
        filter_value: Any
    ) -> List[Dict[str, Any]]:
        """
        Filter schedule data by a specific key-value pair.
        
        Args:
            data: List of schedule dictionaries
            filter_key: Key to filter by
            filter_value: Value to match
            
        Returns:
            Filtered list of dictionaries
        """
        return [record for record in data if record.get(filter_key) == filter_value]
    
    def sort_schedule(
        self,
        data: List[Dict[str, Any]],
        sort_key: str,
        reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Sort schedule data by a specific key.
        
        Args:
            data: List of schedule dictionaries
            sort_key: Key to sort by
            reverse: Sort in reverse order
            
        Returns:
            Sorted list of dictionaries
        """
        return sorted(data, key=lambda x: x.get(sort_key, ""), reverse=reverse)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported report formats.
        
        Returns:
            List of supported format names
        """
        return list(self.generators.keys())


# Example usage and testing
if __name__ == "__main__":
    # Sample schedule data
    sample_data = [
        {
            "ID": 1,
            "Subject": "Mathematics",
            "Instructor": "Prof. Smith",
            "Time": "09:00 AM",
            "Room": "101"
        },
        {
            "ID": 2,
            "Subject": "Physics",
            "Instructor": "Prof. Johnson",
            "Time": "10:30 AM",
            "Room": "102"
        },
        {
            "ID": 3,
            "Subject": "Chemistry",
            "Instructor": "Prof. Davis",
            "Time": "01:00 PM",
            "Room": "103"
        },
        {
            "ID": 4,
            "Subject": "English",
            "Instructor": "Prof. Brown",
            "Time": "02:30 PM",
            "Room": "104"
        },
    ]
    
    # Initialize manager
    manager = ScheduleReportManager()
    
    # Generate reports in different formats
    print("Supported formats:", manager.get_supported_formats())
    print("\n" + "="*70)
    
    # JSON Report
    print("\nJSON Report:")
    print("-"*70)
    json_report = manager.generate_report(sample_data, "json", "Daily Schedule")
    print(json_report)
    
    # CSV Report
    print("\n" + "="*70)
    print("\nCSV Report:")
    print("-"*70)
    csv_report = manager.generate_report(sample_data, "csv")
    print(csv_report)
    
    # Plain Text Report
    print("\n" + "="*70)
    print("\nPlain Text Report:")
    print("-"*70)
    text_report = manager.generate_report(sample_data, "text", "Daily Schedule")
    print(text_report)
    
    # Filtering example
    print("\n" + "="*70)
    print("\nFiltering Example (Room = 102):")
    print("-"*70)
    filtered = manager.filter_schedule(sample_data, "Room", "102")
    filtered_report = manager.generate_report(filtered, "json", "Filtered Schedule")
    print(filtered_report)
    
    # Sorting example
    print("\n" + "="*70)
    print("\nSorting Example (by Subject):")
    print("-"*70)
    sorted_data = manager.sort_schedule(sample_data, "Subject")
    sorted_report = manager.generate_report(sorted_data, "text", "Sorted Schedule")
    print(sorted_report)
