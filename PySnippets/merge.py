def merge_configs(source, target):
    """
    Merge two nested dictionaries, returning a new dictionary.

    This function recursively merges the keys of the first dictionary (source)
    with the keys of the second dictionary (target), creating a new dictionary
    as the result. The input dictionaries remain unchanged.

    At each level of nesting, the function checks the type of value associated
    with each key:
    - If both values are dictionaries, it recursively merges them.
    - If both values are lists, it attempts a pairwise merge of their elements.
      If lists are of different lengths, it merges the elements of the shorter list
      with the corresponding elements of the longer list, and appends any remaining
      elements from the longer list to the result.
    - For any other type of value, or mismatched types, the value from target
      replaces the value from source.

    Parameters:
    source (dict): The first dictionary.
    target (dict): The second dictionary.

    Returns:
    dict: A new dictionary containing the merged keys and values of source and target.
    """

    result = source.copy()
    
    for key, value in target.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                merged_list = []
                max_len = max(len(result[key]), len(value))
                for i in range(max_len):
                    if i < len(result[key]) and i < len(value):
                        if isinstance(result[key][i], dict) and isinstance(value[i], dict):
                            merged_list.append(merge_configs(result[key][i], value[i]))
                        else:
                            merged_list.append(value[i])
                    elif i < len(result[key]):
                        merged_list.append(result[key][i])
                    else:
                        merged_list.append(value[i])
                result[key] = merged_list
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result

