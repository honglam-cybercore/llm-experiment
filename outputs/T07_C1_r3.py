def merge_config(defaults, file_config, env_config, cli_config, schema) -> dict:
    def validate_schema(s):
        if not isinstance(s, dict):
            raise ValueError("Schema must be a dict")
        for key, defn in s.items():
            if not isinstance(key, str):
                raise ValueError("Schema key must be string")
            if not isinstance(defn, dict):
                raise ValueError(f"Schema definition must be dict: {key}")
            if 'type' not in defn:
                raise ValueError(f"Missing 'type': {key}")
            if 'required' not in defn:
                raise ValueError(f"Missing 'required': {key}")
            if defn['type'] not in ('int', 'bool', 'str'):
                raise ValueError(f"Invalid type: {key}")
            if not isinstance(defn['required'], bool):
                raise ValueError(f"'required' must be bool: {key}")

    def flatten(d, parent=''):
        items = []
        for k, v in d.items():
            key = f"{parent}.{k}" if parent else k
            if isinstance(v, dict):
                items.extend(flatten(v, key).items())
            else:
                items.append((key, v))
        return dict(items)

    def unflatten(d):
        res = {}
        for key, val in d.items():
            parts = key.split('.')
            curr = res
            for p in parts[:-1]:
                if p not in curr:
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = val
        return res

    def merge(tgt, src):
        for k, v in src.items():
            if k in tgt and isinstance(tgt[k], dict) and isinstance(v, dict):
                merge(tgt[k], v)
            else:
                tgt[k] = v

    def convert(val, defn):
        typ = defn['type']

        if typ == 'bool':
            if isinstance(val, bool):
                res = val
            elif isinstance(val, str):
                if val.lower() == 'true':
                    res = True
                elif val.lower() == 'false':
                    res = False
                else:
                    raise ValueError(f"Cannot convert to bool: {val}")
            else:
                raise ValueError(f"Cannot convert to bool")
        elif typ == 'int':
            if isinstance(val, int) and not isinstance(val, bool):
                res = val
            elif isinstance(val, str):
                try:
                    res = int(val)
                except ValueError:
                    raise ValueError(f"Cannot convert to int: {val}")
            else:
                raise ValueError(f"Cannot convert to int")
        elif typ == 'str':
            res = str(val) if not isinstance(val, str) else val

        if 'min' in defn and res < defn['min']:
            raise ValueError(f"Value below minimum: {res} < {defn['min']}")
        if 'max' in defn and res > defn['max']:
            raise ValueError(f"Value above maximum: {res} > {defn['max']}")

        return res

    validate_schema(schema)

    merged = {}
    for cfg in [defaults, file_config, env_config, cli_config]:
        if cfg:
            merge(merged, cfg)

    flat = flatten(merged)
    result = {}

    for key, defn in schema.items():
        if key in flat:
            result[key] = convert(flat[key], defn)
        elif defn['required']:
            raise ValueError(f"Required key missing: {key}")

    for key in flat:
        if key not in schema:
            raise ValueError(f"Unknown key: {key}")

    return unflatten(result)
