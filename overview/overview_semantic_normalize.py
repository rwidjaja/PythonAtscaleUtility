# overview_semantic_normalize.py
from collections import defaultdict
from overview.overview_semantic_extract import extract_basic_fields

def normalize_semantic(payload):
    semantic_tables = defaultdict(list)

    # Process dimensions with hierarchies and levels
    if 'dimensions' in payload and 'dimension' in payload['dimensions']:
        for dimension in payload['dimensions']['dimension']:
            dim_data = extract_basic_fields(dimension)
            dim_data['type'] = 'dimension'

            # Process hierarchies within dimension
            if 'hierarchy' in dimension:
                for hierarchy in dimension['hierarchy']:
                    hier_data = extract_basic_fields(hierarchy)
                    hier_data['type'] = 'hierarchy'
                    hier_data['dimension_id'] = dim_data.get('id')
                    hier_data['dimension_name'] = dim_data.get('name')

                    # Process levels within hierarchy
                    if 'level' in hierarchy:
                        for level in hierarchy['level']:
                            level_data = extract_basic_fields(level)
                            level_data['type'] = 'level'
                            level_data['hierarchy_id'] = hier_data.get('id')
                            level_data['hierarchy_name'] = hier_data.get('name')
                            level_data['dimension_id'] = dim_data.get('id')
                            level_data['dimension_name'] = dim_data.get('name')

                            # Extract primary attribute
                            if 'primary-attribute' in level:
                                level_data['primary_attribute'] = level['primary-attribute']

                            semantic_tables['levels'].append(level_data)

                    semantic_tables['hierarchies'].append(hier_data)

            semantic_tables['dimensions'].append(dim_data)

    # Process attributes
    if 'attributes' in payload:
        # Process keyed attributes
        if 'keyed-attribute' in payload['attributes']:
            for attr in payload['attributes']['keyed-attribute']:
                attr_data = extract_basic_fields(attr)
                attr_data['type'] = 'keyed_attribute'
                if 'key-ref' in attr:
                    attr_data['key_ref'] = attr['key-ref']
                semantic_tables['attributes'].append(attr_data)

        # Process attribute keys
        if 'attribute-key' in payload['attributes']:
            for key in payload['attributes']['attribute-key']:
                key_data = extract_basic_fields(key)
                key_data['type'] = 'attribute_key'
                semantic_tables['attribute_keys'].append(key_data)

    # Process datasets with their physical and logical components
    if 'datasets' in payload and 'data-set' in payload['datasets']:
        for dataset in payload['datasets']['data-set']:
            ds_data = extract_basic_fields(dataset)
            ds_data['type'] = 'dataset'

            # Process physical tables
            if 'physical' in dataset and 'tables' in dataset['physical']:
                for table in dataset['physical']['tables']:
                    table_data = {
                        'dataset_id': ds_data.get('id'),
                        'dataset_name': ds_data.get('name'),
                        'schema': table.get('schema'),
                        'table_name': table.get('name')
                    }
                    semantic_tables['physical_tables'].append(table_data)

            # Process physical columns
            if 'physical' in dataset and 'columns' in dataset['physical']:
                for column in dataset['physical']['columns']:
                    col_data = extract_basic_fields(column)
                    col_data['type'] = 'physical_column'
                    col_data['dataset_id'] = ds_data.get('id')
                    col_data['dataset_name'] = ds_data.get('name')
                    if 'type' in column and 'data-type' in column['type']:
                        col_data['data_type'] = column['type']['data-type']
                    semantic_tables['physical_columns'].append(col_data)

            # Process logical key references
            if 'logical' in dataset and 'key-ref' in dataset['logical']:
                for key_ref in dataset['logical']['key-ref']:
                    key_ref_data = extract_basic_fields(key_ref)
                    key_ref_data['type'] = 'logical_key_ref'
                    key_ref_data['dataset_id'] = ds_data.get('id')
                    key_ref_data['dataset_name'] = ds_data.get('name')
                    if 'column' in key_ref:
                        key_ref_data['columns'] = ', '.join(key_ref['column'])
                    semantic_tables['logical_key_refs'].append(key_ref_data)

            # Process logical attribute references
            if 'logical' in dataset and 'attribute-ref' in dataset['logical']:
                for attr_ref in dataset['logical']['attribute-ref']:
                    attr_ref_data = extract_basic_fields(attr_ref)
                    attr_ref_data['type'] = 'logical_attribute_ref'
                    attr_ref_data['dataset_id'] = ds_data.get('id')
                    attr_ref_data['dataset_name'] = ds_data.get('name')
                    if 'column' in attr_ref:
                        attr_ref_data['columns'] = ', '.join(attr_ref['column'])
                    semantic_tables['logical_attribute_refs'].append(attr_ref_data)

            semantic_tables['datasets'].append(ds_data)

    # Process cube measures and attributes
    if 'cubes' in payload and 'cube' in payload['cubes']:
        for cube in payload['cubes']['cube']:
            cube_data = extract_basic_fields(cube)
            cube_data['type'] = 'cube'

            # Process cube attributes (measures)
            if 'attributes' in cube and 'attribute' in cube['attributes']:
                for attr in cube['attributes']['attribute']:
                    attr_data = extract_basic_fields(attr)
                    attr_data['type'] = 'cube_attribute'
                    attr_data['cube_id'] = cube_data.get('id')
                    attr_data['cube_name'] = cube_data.get('name')

                    # Determine if it's a measure
                    if 'properties' in attr and 'type' in attr['properties']:
                        attr_type = attr['properties']['type']
                        if isinstance(attr_type, dict):
                            if 'measure' in attr_type:
                                attr_data['attribute_type'] = 'measure'
                                if 'default-aggregation' in attr_type['measure']:
                                    attr_data['aggregation'] = attr_type['measure']['default-aggregation']
                            elif 'count-distinct' in attr_type:
                                attr_data['attribute_type'] = 'count_distinct_measure'
                            elif 'count-nonnull' in attr_type:
                                attr_data['attribute_type'] = 'count_nonnull_measure'
                            elif 'sum-distinct' in attr_type:
                                attr_data['attribute_type'] = 'sum_distinct_measure'

                    semantic_tables['measures'].append(attr_data)

            # Process cube dimensions
            if 'dimensions' in cube and 'dimension' in cube['dimensions']:
                for dim in cube['dimensions']['dimension']:
                    dim_data = extract_basic_fields(dim)
                    dim_data['type'] = 'cube_dimension'
                    dim_data['cube_id'] = cube_data.get('id')
                    dim_data['cube_name'] = cube_data.get('name')
                    semantic_tables['cube_dimensions'].append(dim_data)

            semantic_tables['cubes'].append(cube_data)

    # Process calculated members
    if 'calculated-members' in payload and 'calculated-member' in payload['calculated-members']:
        for calc_member in payload['calculated-members']['calculated-member']:
            calc_data = extract_basic_fields(calc_member)
            calc_data['type'] = 'calculated_member'
            if 'expression' in calc_member:
                calc_data['expression'] = calc_member['expression']
            semantic_tables['calc_members'].append(calc_data)

    return semantic_tables