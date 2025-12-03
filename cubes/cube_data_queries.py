# tabs/cube_data_queries.py
import requests
import urllib3
from common import load_config, get_instance_type, get_credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# XMLA Query Templates
CATALOG_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
              SELECT [CATALOG_NAME], [CATALOG_GUID] from $system.DBSCHEMA_CATALOGS
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>Default</Catalog>
          <Cube>Default</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

CUBE_QUERY_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
              SELECT [CUBE_NAME], [CUBE_GUID] from $system.MDSCHEMA_CUBES
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>Default</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

# Metadata queries
DIMENSIONS_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
          SELECT [CATALOG_NAME], [CUBE_NAME], [DIMENSION_UNIQUE_NAME], [DIMENSION_CAPTION], [DEFAULT_HIERARCHY] 
          FROM $system.MDSCHEMA_DIMENSIONS 
          WHERE [CUBE_NAME] = '{cube_name}' AND [DIMENSION_UNIQUE_NAME] &lt;&gt; '[Measures]'
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>{cube_name}</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

HIERARCHIES_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
          SELECT [DIMENSION_UNIQUE_NAME], [HIERARCHY_NAME], [HIERARCHY_UNIQUE_NAME], [HIERARCHY_CAPTION], [HIERARCHY_DISPLAY_FOLDER]
          FROM $system.MDSCHEMA_HIERARCHIES 
          WHERE [CUBE_NAME] = '{cube_name}' AND [DIMENSION_UNIQUE_NAME] &lt;&gt; '[Measures]'
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>{cube_name}</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

LEVELS_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
          SELECT [DIMENSION_UNIQUE_NAME], [HIERARCHY_UNIQUE_NAME], [LEVEL_NAME], [LEVEL_UNIQUE_NAME], [LEVEL_CAPTION], [LEVEL_NUMBER]
          FROM $system.MDSCHEMA_LEVELS 
          WHERE [CUBE_NAME] = '{cube_name}' AND [DIMENSION_UNIQUE_NAME] &lt;&gt; '[Measures]' AND [LEVEL_NAME] &lt;&gt; '(All)'
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>{cube_name}</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

MEASURES_QUERY = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
          SELECT [MEASURE_NAME], [MEASURE_UNIQUE_NAME], [MEASURE_CAPTION], [MEASURE_DISPLAY_FOLDER]
          FROM $system.MDSCHEMA_MEASURES 
          WHERE [CUBE_NAME] = '{cube_name}'
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>{cube_name}</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

def run_xmla_query(xml_body: str):
    config = load_config()
    host = config["host"]
    username, password = get_credentials()
    instance_type = get_instance_type()

    if instance_type == "container":
        url = f"https://{host}/engine/xmla"
    else:
        url = f"https://{host}:10502/xmla/default"

    resp = requests.post(
        url,
        data=xml_body.encode("utf-8"),
        headers={"Content-Type": "text/xml"},
        auth=(username, password),
        verify=False
    )
    resp.raise_for_status()
    return resp.text

def build_xmla_request(mdx_query, catalog, cube, use_agg=True, use_cache=True):
    """Build XMLA request from MDX query with flags"""
    # Convert boolean to string for XML
    agg_flag = "true" if use_agg else "false"
    cache_flag = "true" if use_cache else "false"
    
    return f"""<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
<Body>
<Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
<Command>
    <Statement><![CDATA[{mdx_query}]]></Statement>
</Command>
<Properties>
    <PropertyList>
    <Catalog>{catalog}</Catalog>
    <Cube>{cube}</Cube>
    <UseAggs>{agg_flag}</UseAggs>
    <UseQueryCache>{cache_flag}</UseQueryCache>
    </PropertyList>
</Properties>
</Execute>
</Body>
</Envelope>"""