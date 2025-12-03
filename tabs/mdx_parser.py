# tabs/mdx_parser.py
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Any
import re

def parse_xmla_mdx_result(xmla_response: str) -> Optional[pd.DataFrame]:
    """
    Parse XMLA MDX query response into a pandas DataFrame
    Handles the complex XMLA structure with axes, tuples, and cell data
    """
    try:
        if not xmla_response:
            return None
            
        # Parse the XML response
        root = ET.fromstring(xmla_response)
        
        # Define namespaces
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'xmla': 'urn:schemas-microsoft-com:xml-analysis',
            'mddataset': 'urn:schemas-microsoft-com:xml-analysis:mddataset',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        # Register namespaces for easier searching
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)
        
        # Find the root element with the actual data
        root_elem = root.find('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}root')
        if root_elem is None:
            return parse_fallback_mdx(xmla_response)
        
        # Extract axes information
        axes_elem = root_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Axes')
        if axes_elem is None:
            return parse_fallback_mdx(xmla_response)
        
        # Extract cell data
        cell_data_elem = root_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}CellData')
        if cell_data_elem is None:
            return parse_fallback_mdx(xmla_response)
        
        # Parse rows from Axis0 (rows axis)
        rows = parse_axis_data(axes_elem, 'Axis0')
        
        # Parse columns from SlicerAxis (columns axis) 
        columns = parse_axis_data(axes_elem, 'SlicerAxis')
        
        # Parse cell values
        cell_values = parse_cell_data(cell_data_elem)
        
        # Build DataFrame
        if rows and cell_values:
            return build_dataframe_from_axes(rows, columns, cell_values)
        else:
            return parse_fallback_mdx(xmla_response)
            
    except ET.ParseError as e:
        print(f"XML parsing error: {e}")
        return parse_fallback_mdx(xmla_response)
    except Exception as e:
        print(f"Unexpected error parsing MDX result: {e}")
        return parse_fallback_mdx(xmla_response)

def parse_axis_data(axes_elem, axis_name: str) -> List[Dict[str, str]]:
    """Parse data from a specific axis"""
    axis_data = []
    
    axis_elem = axes_elem.find(f'.//{{urn:schemas-microsoft-com:xml-analysis:mddataset}}Axis[@name="{axis_name}"]')
    if axis_elem is None:
        return axis_data
    
    # Find all tuples in this axis
    tuples_elem = axis_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Tuples')
    if tuples_elem is None:
        return axis_data
    
    for tuple_elem in tuples_elem.findall('{urn:schemas-microsoft-com:xml-analysis:mddataset}Tuple'):
        tuple_data = {}
        
        # Extract member information
        members = tuple_elem.findall('{urn:schemas-microsoft-com:xml-analysis:mddataset}Member')
        for i, member_elem in enumerate(members):
            hierarchy = member_elem.get('Hierarchy', f'Column_{i}')
            
            # Extract member properties
            caption_elem = member_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Caption')
            caption = caption_elem.text if caption_elem is not None else f'Member_{i}'
            
            uname_elem = member_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}UName')
            unique_name = uname_elem.text if uname_elem is not None else caption
            
            tuple_data[hierarchy] = caption
            tuple_data[f'{hierarchy}_UniqueName'] = unique_name
        
        if tuple_data:
            axis_data.append(tuple_data)
    
    return axis_data

def parse_cell_data(cell_data_elem) -> List[Dict[str, Any]]:
    """Parse cell data values"""
    cell_values = []
    
    for cell_elem in cell_data_elem.findall('{urn:schemas-microsoft-com:xml-analysis:mddataset}Cell'):
        cell_ordinal = int(cell_elem.get('CellOrdinal', 0))
        
        # Extract cell value
        value_elem = cell_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Value')
        value = None
        if value_elem is not None and value_elem.text:
            value_type = value_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type', 'xsd:string')
            if 'float' in value_type:
                try:
                    value = float(value_elem.text)
                except (ValueError, TypeError):
                    value = value_elem.text
            else:
                value = value_elem.text
        
        # Extract format information
        format_elem = cell_elem.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}FormatString')
        format_string = format_elem.text if format_elem is not None else None
        
        cell_values.append({
            'ordinal': cell_ordinal,
            'value': value,
            'format': format_string
        })
    
    # Sort by ordinal
    cell_values.sort(key=lambda x: x['ordinal'])
    return cell_values

def build_dataframe_from_axes(rows: List[Dict], columns: List[Dict], cell_values: List[Dict]) -> pd.DataFrame:
    """Build DataFrame from parsed axis and cell data"""
    
    if not rows:
        return pd.DataFrame()
    
    # Create row data
    row_data = []
    for i, row in enumerate(rows):
        row_entry = {}
        
        # Add row dimension data
        for key, value in row.items():
            if not key.endswith('_UniqueName'):  # Skip unique names for display
                row_entry[key] = value
        
        # Add cell values
        if i < len(cell_values):
            row_entry['Value'] = cell_values[i]['value']
            if cell_values[i]['format']:
                row_entry['Format'] = cell_values[i]['format']
        
        row_data.append(row_entry)
    
    # Create DataFrame
    df = pd.DataFrame(row_data)
    
    # If we have multiple value columns, handle them properly
    if 'Value' in df.columns and len(df.columns) > 1:
        # Reorder columns to put Value last for better readability
        cols = [col for col in df.columns if col != 'Value'] + ['Value']
        df = df[cols]
    
    return df

def parse_fallback_mdx(xmla_response: str) -> Optional[pd.DataFrame]:
    """Fallback parsing method for MDX results"""
    try:
        # Try to extract any tabular data using simpler methods
        lines = xmla_response.split('\n')
        data_lines = []
        
        # Look for patterns that indicate data
        for line in lines:
            clean_line = line.strip()
            
            # Skip XML tags and look for data content
            if (clean_line and 
                not clean_line.startswith('<?') and
                not clean_line.startswith('<') and
                not clean_line.endswith('>') and
                len(clean_line) > 1):
                data_lines.append(clean_line)
        
        if data_lines:
            # Try to detect structure
            if any('|' in line for line in data_lines):
                # Pipe-separated data
                rows = []
                for line in data_lines:
                    if '|' in line:
                        rows.append([x.strip() for x in line.split('|')])
                
                if rows:
                    # Use first row as header if it looks like headers
                    if all(not cell.strip().isdigit() for cell in rows[0] if cell.strip()):
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                    else:
                        df = pd.DataFrame(rows)
                    return df
            else:
                # Single column data
                df = pd.DataFrame(data_lines, columns=['Result'])
                return df
        
        # Last resort: extract all text content between tags
        text_content = re.sub(r'<[^>]+>', ' ', xmla_response)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        if len(text_content) > 10:  # Only if we have meaningful content
            words = text_content.split()
            # Create a simple DataFrame with the content
            df = pd.DataFrame([{'Content': text_content[:200] + '...' if len(text_content) > 200 else text_content}])
            return df
            
        return None
        
    except Exception as e:
        print(f"Error in fallback parsing: {e}")
        return None

# tabs/mdx_parser.py (updated debug function)
def debug_xmla_response(xmla_response: str) -> Dict[str, Any]:
    """Debug function to analyze XMLA response structure - returns cleaner info"""
    debug_info = {
        'response_length': len(xmla_response),
        'has_soap_envelope': 'soap:Envelope' in xmla_response,
        'has_cell_data': 'CellData' in xmla_response,
        'has_tuple': 'Tuple' in xmla_response,
        'has_axis': 'Axis' in xmla_response
    }
    
    try:
        root = ET.fromstring(xmla_response)
        namespaces = {'mddataset': 'urn:schemas-microsoft-com:xml-analysis:mddataset'}
        
        # Count tuples and cells
        tuples = root.findall('.//mddataset:Tuple', namespaces)
        cells = root.findall('.//mddataset:Cell', namespaces)
        debug_info['tuple_count'] = len(tuples)
        debug_info['cell_count'] = len(cells)
        
    except:
        debug_info['parse_error'] = True
    
    return debug_info

# Update the main parse function to use the new XMLA parser
def parse_mdx_result(xmla_response: str) -> Optional[pd.DataFrame]:
    """Main MDX parsing function - uses XMLA-specific parser"""
    return parse_xmla_mdx_result(xmla_response)