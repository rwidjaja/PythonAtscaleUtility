# tabs/cube_data_parsers.py
import xml.etree.ElementTree as ET
import pandas as pd

def parse_rows(xml_text, columns):
    """Parse XML response into DataFrame - FIXED for actual SOAP response"""
    try:
        root = ET.fromstring(xml_text)
        
        # Define namespaces from your SOAP response
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'rowset': 'urn:schemas-microsoft-com:xml-analysis:rowset'
        }
        
        rows = []
        # Find all row elements in the rowset namespace
        for row_elem in root.findall('.//rowset:row', namespaces):
            row_data = {}
            for col in columns:
                # Look for the column in the rowset namespace
                elem = row_elem.find(f'rowset:{col}', namespaces)
                row_data[col] = elem.text if elem is not None else None
            rows.append(row_data)
        
        return pd.DataFrame(rows)
    
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return pd.DataFrame()

def parse_catalogs(xml_text: str):
    """Parse catalogs from SOAP response - returns list of dicts with name and guid"""
    try:
        root = ET.fromstring(xml_text)
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'rowset': 'urn:schemas-microsoft-com:xml-analysis:rowset'
        }
        
        catalogs = []
        for row in root.findall('.//rowset:row', namespaces):
            name_elem = row.find('rowset:CATALOG_NAME', namespaces)
            guid_elem = row.find('rowset:CATALOG_GUID', namespaces)
            
            if name_elem is not None:
                catalog_info = {
                    'name': name_elem.text,
                    'guid': guid_elem.text if guid_elem is not None else None
                }
                catalogs.append(catalog_info)
        
        return catalogs
    except Exception as e:
        print(f"Error parsing catalogs: {e}")
        return []

def parse_cubes(xml_text: str):
    """Parse cubes from SOAP response - returns list of dicts with name and guid"""
    try:
        root = ET.fromstring(xml_text)
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'rowset': 'urn:schemas-microsoft-com:xml-analysis:rowset'
        }
        
        cubes = []
        for row in root.findall('.//rowset:row', namespaces):
            name_elem = row.find('rowset:CUBE_NAME', namespaces)
            guid_elem = row.find('rowset:CUBE_GUID', namespaces)
            
            if name_elem is not None:
                cube_info = {
                    'name': name_elem.text,
                    'guid': guid_elem.text if guid_elem is not None else None
                }
                cubes.append(cube_info)
        
        return cubes
    except Exception as e:
        print(f"Error parsing cubes: {e}")
        return []
    
def parse_xmla_result_to_dataframe(xml_text):
    """Parse XMLA SOAP response into a pandas DataFrame - IMPROVED with proper captions"""
    try:
        # Parse the XML
        root = ET.fromstring(xml_text)
        
        # Define namespaces
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            'msxmla': 'http://schemas.microsoft.com/analysisservices/2003/xmla',
            '': 'urn:schemas-microsoft-com:xml-analysis:mddataset'
        }
        
        # Find the root element with the data
        data_root = root.find('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}root')
        if data_root is None:
            return pd.DataFrame()
        
        # Extract column headers (from Axis0 - COLUMNS) - USING CAPTIONS
        column_headers = []
        axis0 = data_root.find('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Axis[@name="Axis0"]')
        if axis0 is not None:
            tuples = axis0.findall('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Tuple')
            for tuple_elem in tuples:
                members = tuple_elem.findall('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Member')
                if members:
                    # For multiple measures, combine their CAPTIONS (not unique names)
                    captions = []
                    for member in members:
                        caption_elem = member.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Caption')
                        if caption_elem is not None and caption_elem.text:
                            # Use the caption for display
                            captions.append(caption_elem.text)
                        else:
                            # Fallback: try to extract from unique name
                            uname_elem = member.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}UName')
                            if uname_elem is not None and uname_elem.text:
                                # Extract measure name from unique name like [Measures].[salesamount1]
                                parts = uname_elem.text.split('.')
                                if len(parts) >= 2:
                                    measure_name = parts[-1].replace(']', '')
                                    captions.append(measure_name)
                                else:
                                    captions.append(uname_elem.text)
                    if captions:
                        column_headers.append(' - '.join(captions))
                    else:
                        column_headers.append('Measure')
        
        # Extract row data (from Axis1 - ROWS) - USING CAPTIONS
        rows_data = []
        axis1 = data_root.find('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Axis[@name="Axis1"]')
        if axis1 is not None:
            tuples = axis1.findall('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Tuple')
            for tuple_elem in tuples:
                row_data = {}
                members = tuple_elem.findall('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Member')
                
                # Extract row labels from members USING CAPTIONS
                row_labels = []
                for i, member in enumerate(members):
                    caption_elem = member.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Caption')
                    if caption_elem is not None and caption_elem.text:
                        row_labels.append(caption_elem.text)
                    else:
                        # Fallback: use unique name
                        uname_elem = member.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}UName')
                        if uname_elem is not None and uname_elem.text:
                            # Extract member name from unique name
                            parts = uname_elem.text.split('.')
                            if len(parts) >= 2:
                                member_name = parts[-1].replace(']', '').replace('&amp;', '')
                                row_labels.append(member_name)
                            else:
                                row_labels.append(uname_elem.text)
                        else:
                            row_labels.append(f'Dimension_{i}')
                
                # Store the combined row label
                if row_labels:
                    row_data['Row_Label'] = ' - '.join(row_labels)
                else:
                    row_data['Row_Label'] = 'All'
                
                rows_data.append(row_data)
        
        # Extract cell data and map to rows
        cell_data_elem = data_root.find('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}CellData')
        if cell_data_elem is not None:
            cells = cell_data_elem.findall('.//{urn:schemas-microsoft-com:xml-analysis:mddataset}Cell')
            
            # Calculate dimensions
            num_cols = len(column_headers) if column_headers else 1
            num_rows = len(rows_data)
            
            if num_rows > 0:
                # Map cells to rows and columns
                for cell_ordinal, cell in enumerate(cells):
                    row_idx = cell_ordinal // num_cols
                    col_idx = cell_ordinal % num_cols
                    
                    if row_idx < num_rows:
                        # Try to get formatted value first, then raw value
                        fmt_value_elem = cell.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}FmtValue')
                        value_elem = cell.find('{urn:schemas-microsoft-com:xml-analysis:mddataset}Value')
                        
                        if fmt_value_elem is not None and fmt_value_elem.text:
                            cell_value = fmt_value_elem.text
                        elif value_elem is not None and value_elem.text:
                            cell_value = value_elem.text
                        else:
                            cell_value = ''
                        
                        # Use column header if available, otherwise generic name
                        if col_idx < len(column_headers):
                            col_name = column_headers[col_idx]
                        else:
                            col_name = f'Column_{col_idx}'
                        
                        rows_data[row_idx][col_name] = cell_value
        
        # Create DataFrame
        if rows_data:
            df = pd.DataFrame(rows_data)
            
            # Set Row_Label as index if it exists
            if 'Row_Label' in df.columns:
                df = df.set_index('Row_Label')
            
            return df
        else:
            return pd.DataFrame()
        
    except Exception as e:
        print(f"Error parsing XMLA result: {e}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()