# tabs/common_xmla.py

SOAP_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Execute xmlns="urn:schemas-microsoft-com:xml-analysis">
      <Command>
        <Statement>
          {sql}
        </Statement>
      </Command>
      <Properties>
        <PropertyList>
          <Catalog>{catalog}</Catalog>
          <Cube>{cube}</Cube>
        </PropertyList>
      </Properties>
    </Execute>
  </soap:Body>
</soap:Envelope>"""

def build_xmla_query(sql: str, catalog: str, cube: str) -> str:
    """Wrap a SQL fragment in the standard XMLA SOAP envelope."""
    return SOAP_TEMPLATE.format(sql=sql.strip(), catalog=catalog, cube=cube)